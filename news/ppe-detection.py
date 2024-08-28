import pika
import cv2
import numpy as np
import sqlite3
import os
import json
import requests
from threading import Thread
import tensorflow as tf

class PPEDetectionService:
    def __init__(self, queue_name, db_path, rabbitmq_host):
        self.queue_name = queue_name
        self.db_path = db_path
        self.rabbitmq_host = rabbitmq_host
        self.connection = None
        self.channel = None
        self.is_running = False
        self.model = self.load_model()

    def load_model(self):
        # Load your PPE detection model here
        # This is a placeholder. Replace with your actual model loading code.
        return tf.keras.applications.MobileNetV2(weights='imagenet')

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

            # Preprocess the image for the model
            resized_frame = cv2.resize(frame, (224, 224))
            input_frame = tf.keras.applications.mobilenet_v2.preprocess_input(resized_frame[np.newaxis, ...])

            # Perform PPE detection
            predictions = self.model.predict(input_frame)
            decoded_predictions = tf.keras.applications.mobilenet_v2.decode_predictions(predictions.numpy())

            # This is a simplification. In a real scenario, you'd have a model specifically trained for PPE detection.
            ppe_detected = any('helmet' in pred[1] or 'vest' in pred[1] for pred in decoded_predictions[0])

            # Store results in SQLite database
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS ppe_detection_results
                         (timestamp TEXT, ppe_detected INTEGER)''')
            c.execute("INSERT INTO ppe_detection_results VALUES (datetime('now'), ?)", 
                      (int(ppe_detected),))
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
            requests.post('http://error-logging:5000/log', json={'service': 'ppe-detection', 'message': message})
        except:
            print(f"Failed to log error: {message}")

if __name__ == "__main__":
    queue_name = os.environ.get('QUEUE_NAME')
    db_path = os.environ.get('DB_PATH')
    rabbitmq_host = os.environ.get('RABBITMQ_HOST')
    
    ppe_detection_service = PPEDetectionService(queue_name, db_path, rabbitmq_host)
    service_thread = Thread(target=ppe_detection_service.run)
    service_thread.start()

    try:
        service_thread.join()
    except KeyboardInterrupt:
        print("Stopping PPE detection service...")
        ppe_detection_service.stop()
        service_thread.join()
