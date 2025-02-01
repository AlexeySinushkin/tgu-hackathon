from ultralytics import YOLO
import cv2
import numpy as np
import io
# # Load the pretrained YOLOv8 Nano model
# model = YOLO("yolo11n_road_damage.pt")
#
# # Perform predictions on an image
# results = model.predict(source="test1.png", save=True, imgsz=640)
#
# # Process prediction results
# for result in results:  # Iterate through results (one per image)
#     print("Results for image:", result.path)  # Path to the image
#     boxes = result.boxes  # List of all detected objects (bounding boxes)
#     for box in boxes:
#         cls = int(box.cls.cpu().numpy().item())  # Class of the object (scalar)
#         conf = float(box.conf.cpu().numpy().item())  # Confidence of the prediction (scalar)
#         coords = box.xyxy.cpu().numpy()  # Coordinates of the bounding box (x1, y1, x2, y2)
#         print(f"Class: {cls}, Confidence: {conf:.2f}, Coordinates: {coords}")

class NeuroImageHandler():
    def __init__(self):
        self.model = YOLO("handler/yolo11n_road_damage.pt")

    def process_image(self, image_bytes: bytes) -> list:
        # Преобразуем байты изображения в numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        # Декодируем изображение с помощью OpenCV
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        # Выполняем предсказание с использованием модели YOLO
        results = self.model.predict(source=img, save=True, imgsz=640)
        all_boxes = []
        for result in results:
            boxes = result.boxes  # Список всех обнаруженных объектов (bounding boxes)
            all_boxes.extend(boxes)
        return all_boxes