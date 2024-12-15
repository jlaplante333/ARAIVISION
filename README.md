# ARAIVISION
AI AR Vision 


Instructions to run/ Explanation of files: 

Blind.zip --> Please extract this and follow instructions to run this code on a VisionPro locally. VisionPro does not allow frames to be exported due to Apple privacy policies, therefore we had to write the object detection for VisionPro inside the App from scratch and could not reuse our depth perception algorithm in our python app server.

app.py --> This is the server side logic for sending our image frames to our server.py application, where we run our depth perception algorithm that takes 2d images and then uses a deep learning model to measure the depth towards different objects (a 2d image to 3d conversion with depth map conversion.) We open a websockets connection for a real-time connection to the server. This can be run locally or over the internet as a web app. 

templates/index.html --> This is the html for the browser side for the mobile and web app. User will click "start streaming" and it will stream from their camera 20 FPS raw image data and send these images to the server side logic to process. 
