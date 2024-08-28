import pika
import cv2
import numpy as np
import sqlite3
import os
import json
import requests
from threading import Thread
import face_recognition

class FaceRecognitionService:
    def __init__(self, queue_name, db_path, rabbitmq_host):
        self.queue_name = queue_name
        self.db_path = db_path
        self.rabbitmq_host = rabbitmq_host
        self.connection = None
        self.channel = None
        self.is_running = False

    def connect_to_rabbitmq(self):
        while True:
            try:
                self.connection = pika.BlockingConnection(pika.ConnectionParameters(self.rabbitmq_host))
                self.channel = self.connection.channel()
                self.channel.queue_declare(queue=self.queue_name)
                print("Connected to RabbitMQ")
                return
            except Exception as e:
                self.log_error(f"Failed to connect to RabbitMQ: {e}")
                time.sleep(5)

    def process_frame(self, ch, method, properties, body):
        try:
            # Convert the byte string to a numpy array
            nparr = np.frombuffer(body, np.uint8)
            # Decode the numpy array to an image
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Perform face recognition
            face_locations = face_recognition.face_locations(frame)
            face_encodings = face_recognition.face_encodings(frame, face_locations)

            # Store results in SQLite database
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS face_recognition_results
                         (timestamp TEXT, num_faces INTEGER)''')
            c.execute("INSERT INTO face_recognition_results VALUES (datetime('now'), ?)", 
                      (len(face_locations),))
            conn.commit()
            conn.close()

        except Exception as e:
            self.log_error(f"Error processing frame: {e}")

    def run(self):
        self.is_running = True
        while self.is_running:
            if not self.connection or self.connection.is_closed:
                self.connect_to_rabbitmq()

            try:
                self.channel.basic_consume(queue=self.queue_name, 
                                           on_message_callback=self.process_frame, 
                                           auto_ack=True)
                print("Waiting for frames. To exit press CTRL+C")
                self.channel.start_consuming()
            except Exception as e:
                self.log_error(f"Error consuming messages: {e}")
                time.sleep(5)

    def stop(self):
        self.is_running = False
        if self.connection:
            self.connection.close()

    def log_error(self, message):
        try:
            requests.post('http://error-logging:5000/log', json={'service': 'face-recognition', 'message': message})
        except:
            print(f"Failed to log error: {message}")

if __name__ == "__main__":
    queue_name = os.environ.get('QUEUE_NAME')
    db_path = os.environ.get('DB_PATH')
    rabbitmq_host = os.environ.get('RABBITMQ_HOST')
    
    face_recognition_service = FaceRecognitionService(queue_name, db_path, rabbitmq_host)
    service_thread = Thread(target=face_recognition_service.run)
    service_thread.start()

    try:
        service_thread.join()
    except KeyboardInterrupt:
        print("Stopping face recognition service...")
        face_recognition_service.stop()
        service_thread.join()
