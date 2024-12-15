import asyncio
import os
import ssl
from flask import Flask, render_template, jsonify, request
import threading
import websockets
from io import BytesIO
from PIL import Image

app = Flask(__name__)
loop = asyncio.new_event_loop()

FRIEND_URI = "ws://192.168.0.8:8765"  # Your friend's WebSocket server URI

# Initialize a global frame counter
frame_count = 0

# Lock to ensure thread-safe incrementing of frame_count
frame_lock = threading.Lock()

# Streaming control flag
streaming_event = threading.Event()

def start_event_loop(loop):
    """Start the asyncio event loop in a separate thread."""
    asyncio.set_event_loop(loop)
    loop.run_forever()

# Start the event loop in a background thread
event_loop_thread = threading.Thread(target=start_event_loop, args=(loop,), daemon=True)
event_loop_thread.start()

async def send_frame_to_friend(img_bytes):
    """Send binary image data to the friend's WebSocket server."""
    try:
        async with websockets.connect(FRIEND_URI) as websocket:
            await websocket.send(img_bytes)  # Send binary data directly
            print(f"Sent frame of size {len(img_bytes)} bytes.")
            # Optionally, wait for a response from the server
            response = await websocket.recv()
            print(f"Received response from friend: {response}")
    except Exception as e:
        print("Error sending frame to friend:", e)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_stream', methods=['POST'])
def start_stream():
    """Start streaming images to the friend's WebSocket server."""
    if not streaming_event.is_set():
        streaming_event.set()
        print("Streaming has been started.")
        return jsonify({"status": "Streaming started."})
    else:
        return jsonify({"status": "Already streaming."})

@app.route('/stop_stream', methods=['POST'])
def stop_stream():
    """Stop streaming images to the friend's WebSocket server."""
    if streaming_event.is_set():
        streaming_event.clear()
        print("Streaming has been stopped.")
        return jsonify({"status": "Streaming stopped."})
    else:
        return jsonify({"status": "Streaming is not active."})

@app.route('/upload_frame', methods=['POST'])
def upload_frame():
    """Handle incoming image frames, save them, and forward to the friend's server if streaming is active."""
    global frame_count
    if 'image' not in request.files:
        return jsonify({"status": "No image part in the request"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"status": "No selected file"}), 400

    if file and allowed_file(file.filename):
        try:
            img_bytes = file.read()
            # Verify it's a PNG by opening with PIL
            img = Image.open(BytesIO(img_bytes))
            if img.format != 'PNG':
                return jsonify({"status": "Invalid image format. Only PNG images are allowed."}), 400
        except Exception as e:
            print(f"Error reading image file: {e}")
            return jsonify({"status": "Failed to read the image file."}), 400

        # Generate a unique filename with less than 10 characters (including .png)
        with frame_lock:
            frame_count += 1
            if frame_count > 9999:
                frame_count = 1  # Reset counter after 9999 to avoid overflow
            filename = f"{frame_count:04}.png"  # e.g., '0001.png', '0002.png', ...

        # Save the image locally
        try:
            with open(filename, "wb") as f:
                f.write(img_bytes)
            print(f"Received and saved a new PNG frame as {filename}.")
        except IOError as e:
            print(f"Error saving file {filename}: {e}")
            return jsonify({"status": "Failed to save the frame."}), 500

        # Now send this frame to your friend's server only if streaming is active
        if streaming_event.is_set():
            asyncio.run_coroutine_threadsafe(send_frame_to_friend(img_bytes), loop)
            return jsonify({"status": f"Frame {filename} received and forwarded to friend."})
        else:
            print(f"Frame {filename} received but streaming is not active.")
            return jsonify({"status": f"Frame {filename} received but streaming not active."})
    else:
        return jsonify({"status": "Invalid file type. Only PNG images are allowed."}), 400

def allowed_file(filename):
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.lower().endswith('.png')

if __name__ == '__main__':
    # Ensure the directory exists where images will be saved
    os.makedirs('.', exist_ok=True)  # Current directory; change as needed

    # Configure SSL context
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile='cert.pem', keyfile='key.pem')  # Ensure these files exist
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False, ssl_context=context)
