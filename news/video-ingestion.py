import cv2
import pika
import json
import time
import os
import requests
from threading import Thread

class VideoIngestion:
    def __init__(self, camera_url, queue_name, rabbitmq_host):
        self.camera_url = camera_url
        self.queue_name = queue_name
        self.rabbitmq_host = rabbitmq_host
        self.connection = None
        self.channel = None
        self.cap = None
        self.is_running = False

    def connect_to_camera(self):
        while True:
            try:
                self.cap = cv2.VideoCapture(self.camera_url)
                if self.cap.isOpened():
                    print(f"Connected to camera: {self.camera_url}")
                    return
            except Exception as e:
                self.log_error(f"Failed to connect to camera: {e}")
                time.sleep(5)

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

    def publish_frame(self, frame):
        _, buffer = cv2.imencode('.jpg', frame)
        self.channel.basic_publish(exchange='',
                                   routing_key=self.queue_name,
                                   body=buffer.tobytes())

    def run(self):
        self.is_running = True
        while self.is_running:
            if not self.cap or not self.cap.isOpened():
                self.connect_to_camera()
            
            if not self.connection or self.connection.is_closed:
                self.connect_to_rabbitmq()

            ret, frame = self.cap.read()
            if ret:
                self.publish_frame(frame)
            else:
                self.log_error("Failed to get frame, reconnecting...")
                self.cap.release()
                self.connect_to_camera()

            time.sleep(0.1)  # Adjust frame rate as needed

    def stop(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
        if self.connection:
            self.connection.close()

    def log_error(self, message):
        try:
            requests.post('http://error-logging:5000/log', json={'service': 'video-ingestion', 'message': message})
        except:
            print(f"Failed to log error: {message}")

if __name__ == "__main__":
    camera_url = os.environ.get('CAMERA_URL')
    queue_name = os.environ.get('QUEUE_NAME')
    rabbitmq_host = os.environ.get('RABBITMQ_HOST')
    
    ingestion = VideoIngestion(camera_url, queue_name, rabbitmq_host)
    ingestion_thread = Thread(target=ingestion.run)
    ingestion_thread.start()

    try:
        ingestion_thread.join()
    except KeyboardInterrupt:
        print("Stopping video ingestion...")
        ingestion.stop()
        ingestion_thread.join()
