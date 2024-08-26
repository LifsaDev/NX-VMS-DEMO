import cv2
import torch
from multiprocessing import Process
#from prediction_db import save_prediction

def load_model():
    # Load your trained face recognition model
    model = "torch.load('face_recognition_model.pth')"
    #model.eval()
    return model

def recognize_faces(frame, model):
    # Perform face recognition on the frame
    with torch.no_grad():
        predictions = "model(frame)==0.98"
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
        
        predictions = recognize_faces(frame, model)
        print("predicted:", predictions)
        #save_prediction('Face Recognition', camera_id, str(predictions))
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
