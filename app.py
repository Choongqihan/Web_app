from flask import (
    Flask,
    render_template,
    redirect,  # Added redirect for the back button functionality
    url_for,
      send_file,  # Added url_for for the back button functionality
)  
from flask_socketio import (
    SocketIO,
    emit,
)  
from threading import (
    Thread,
    Event,
    Lock,
)  
from datetime import datetime  # Import datetime to generate timestamps
from ultralytics import YOLO  # Import YOLO model from ultralytics for object detection  
import cv2   # Import OpenCV for image and video processing
import os  # Import os for file and directory operations 
import sqlite3

async_mode = None
app = Flask(__name__, template_folder="templates")  # Initialize Flask with the templates folder
socketio = SocketIO(app, async_mode=async_mode)  
thread = None
thread_lock = Lock()

stop_event = Event()  # Create an event to signal when to stop the video capture thread
camera = None  # Initialize camera variable to None, to be set when the camera is initialized

recording_allowed = True

# Function to initialize the camera
def init_camera():
    global camera # Access the global camera variable
    if camera is None:  # Check if the camera has not been initialized
        camera = cv2.VideoCapture(0)  # Open the default camera
        # Set the frame width and height to 640x480 for consistency
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Function to save the current frame and process it with YOLO
def save_current_frame(frame):
    if not os.path.exists("inputs"):  # Check if the 'inputs' directory doesn't exist
        os.makedirs("inputs")  # Create the 'inputs' directory

    timestamp = datetime.now().strftime(
        "%H-%M-%S-%d-%m-%Y"
    )  # Generate a timestamp for the filename
    filename = f"{timestamp}.jpg"  # Create a filename with the timestamp
    input_path = f"inputs/{filename}"  # Define the full path for the input image
    cv2.imwrite(input_path, frame)  # Save the frame to the 'inputs' directory

    model = YOLO("best.pt")  # Initialize the YOLO model with the specified weights
    results = model(input_path)  # Perform object detection on the input image

    if not os.path.exists("outputs"):  # Check if the 'outputs' directory doesn't exist
        os.makedirs("outputs")  # Create the 'outputs' directory

    # Assuming the results contain multiple objects, iterate through them
    for r in results:
        im_array = r.plot()  # Generate an annotated image with the detection results
        output_path = f"outputs/{filename}"  # Define the full path for the output image
        cv2.imwrite(output_path, im_array)  # Save the annotated image to the 'outputs' directory
    return im_array  # Return the processed frame

# Function to capture frames from the camera and emit them to the clients
def capture_frames():
    init_camera()  # Initialize the camera

    try:
        while not stop_event.is_set():  # Loop until the stop event is signaled
            success, frame = camera.read()  # Read the next frame from the camera
            if (
                not success
            ):  # If the frame could not be read successfully, exit the loop
                break

            encode_param = [
                int(cv2.IMWRITE_JPEG_QUALITY),
                85,
            ]  # Set JPEG quality for encoding the frame
            _, buffer = cv2.imencode(
                ".jpg", frame, encode_param
            )  # Encode the frame as JPEG
            socketio.emit(
                "video_frame", buffer.tobytes()
            )  # Emit the encoded frame to clients
    except Exception as e:
        print(
            f"Error capturing video: {e}"
        )  # Print any errors that occur during video capture
  
def background_thread():
    global recording_allowed
    count = 0
    while recording_allowed:
        socketio.sleep(3)
        count += 1
        # Simulated values for chicken and pig confidence
        chicken_confidence = 0.75
        pig_confidence = 0.85
        socketio.emit('chicken_response', {'data': f"Chicken Confidence: {chicken_confidence}", 'count': count})
        socketio.emit('pig_response', {'data': f"Pig Confidence: {pig_confidence}", 'count': count})

# Function to start the video capture in a separate thread
def start_capture():
    stop_event.clear()  # Clear the stop event in case it was set previously
    Thread(
        target=capture_frames
    ).start()  # Start the capture_frames function in a new thread


# Function to stop video capture and release the camera resource
def stop_capture():
    stop_event.set()  # Set the stop event to signal the capture_frames thread to stop
    if camera is not None:  # If the camera has been initialized
        camera.release()  # Release the camera resource

@app.route("/")
def home():
    return render_template("index.html")  

# SocketIO event handler to start video capture
@socketio.on("start_video")
def handle_start_video():
    start_capture()  # Call the start_capture function

# SocketIO event handler to capture a single image
@socketio.on("capture_image")
def handle_capture_image():
    if camera is not None:  # If the camera has been initialized
        success, frame = camera.read()  # Read a frame from the camera
        if success:  # If the frame was read successfully
            processed_frame = save_current_frame(frame)  # Process the frame and get the processed frame
            buffer = cv2.imencode(".jpg", processed_frame)[1]  # Encode the processed frame as JPEG
            with sqlite3.connect('captured_images.db') as conn:
                c = conn.cursor()
                c.execute("INSERT INTO images (data) VALUES (?)", (buffer.tobytes(),))
                conn.commit()

@socketio.on('connect')
def handle_connect():
    emit('connected_response', {'data': 'Connected', 'count': 0})

@socketio.on('connect_button_clicked')
def handle_connect_button():
    global thread, recording_allowed
    with thread_lock:
        if recording_allowed and thread is None:
            thread = socketio.start_background_task(background_thread)
            emit('connect_message', {'data': 'Recording started'})
        elif not recording_allowed:
            recording_allowed = True
            thread = socketio.start_background_task(background_thread)
            emit('connect_message', {'data': 'Recording resumed'})
            emit('connect_message', {'data': 'Recording started again'})
        else:
            emit('connect_message', {'data': 'Recording already started'})

@socketio.on('disconnect_button_clicked')
def handle_disconnect_button():
    global recording_allowed, thread
    recording_allowed = False
    emit('disconnect_message', {'data': 'Recording stopped'})
    thread = None

@socketio.on('resume_recording')
def handle_resume_recording():
    global recording_allowed, thread
    recording_allowed = True  
    with thread_lock:
        if thread is None:  
            thread = socketio.start_background_task(background_thread)
            emit('connect_message', {'data': 'Recording restarted'})
        else:
            emit('connect_message', {'data': 'Recording already running'})

    emit('resume_message', {'data': 'Recording resumed'})

@app.route('/reset_database')
def reset_database():
    try:
        conn = sqlite3.connect('captured_images.db')
        c = conn.cursor()
        c.execute('DROP TABLE IF EXISTS images')
        c.execute('''CREATE TABLE IF NOT EXISTS images
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, data BLOB)''')
        conn.commit()
        conn.close()

        return 'Database reset successfully'
    except Exception as e:
        return 'Error resetting database: {}'.format(e)
    

@app.route("/camera")
def image():
    return render_template("index2.html")  # Serve the index2.html file

@app.route("/back")  # Added route for the back button functionality
def back():
    return redirect(url_for('home'))  # Redirect to the home page

@app.route('/download_image/<int:image_id>')
def download_image(image_id):
    # Connect to your SQLite database
    conn = sqlite3.connect('captured_images.db')  # Replace with your actual database path
    cursor = conn.cursor()

    # Select the image data from the database for a specific id
    cursor.execute("SELECT data FROM images WHERE id=?", (image_id,))

    # Fetch the result
    image_data = cursor.fetchone()
    if image_data is None:
        conn.close()
        return "Image not found", 404

    # Define the path where you want to save the image
    desktop_path = 'C:\\Users\\CHOT\\Desktop'
    filename = f'image_{image_id}.jpg'
    file_path = os.path.join(desktop_path, filename)

    # Write the image data to a file on the desktop
    with open(file_path, 'wb') as file:
        file.write(image_data[0])

    # Close the database connection
    conn.close()

    return send_file(file_path, as_attachment=True)


# Main entry point for the Flask application
if __name__ == "__main__":
    socketio.run(
        app, host="0.0.0.0", debug=True
    )  # Run the Flask app with SocketIO on host 0.0.0.0