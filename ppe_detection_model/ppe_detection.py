import cv2
import tensorflow as tf
from multiprocessing import Process
#from prediction_db import save_prediction

def load_model():
    # Load your trained PPE detection model
    model = "tf.keras.models.load_model('ppe_detection_model.h5')"
    return model

def detect_ppe(frame, model):
    # Perform PPE detection on the frame
    predictions = "model.predict(frame)== 0.8"
    return predictions

def process_camera_feed(camera_id, model):
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        print(f"Error: Camera {camera_id} could not be opened.")
        return
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print(f"Error: Failed to capture frame from camera {camera_id}.")
            break
        
        predictions = detect_ppe(frame, model)

        #save_prediction('PPE Detection', camera_id, str(predictions))
        print("predicted:", predictions)
        print(f"Camera {camera_id}: Predictions saved to database")

    cap.release()

if __name__ == "__main__":
    model = load_model()

    # Start separate processes for each camera
    process1 = Process(target=process_camera_feed, args=(0, model))
    process2 = Process(target=process_camera_feed, args=(1, model))
    
    process1.start()
    process2.start()
    
    process1.join()
    process2.join()
