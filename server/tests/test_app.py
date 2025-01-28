import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from app.main import app  # Предположим, что ваш файл с FastAPI называется main.py

# Создаём клиента для тестирования
client = TestClient(app)

def test_root():
    """
    Тест для эндпоинта "/"
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_server_info():
    """
    Тест для эндпоинта "/info"
    """
    response = client.get("/info")
    assert response.status_code == 200
    assert response.json() == {
        "serverName": "cvHandler",
        "serverVersion": "1.0.0"
    }

def test_db_test_connection():
    """
    Тест для проверки доступности базы данных через "/db-test".
    """
    response = client.get("/db-test")
    assert response.status_code == 200
    assert isinstance(response.json(), bool)  # Проверяем, что ответ True или False

def test_upload_image():
    """
    Тест для загрузки изображения через "/upload-image".
    """
    # Создаём тестовое изображение (чёрный квадрат)
    image = (np.zeros((100, 100, 3), dtype=np.uint8) * 255).astype(np.uint8)
    _, image_bytes = cv2.imencode(".png", image)

    files = {"file": ("test.png", image_bytes.tobytes(), "image/png")}
    response = client.put("/upload-image", files=files)
    assert response.status_code == 200
    assert "imgDB_ID" in response.headers  # Проверяем, что ID вернулся

def test_filters():
    """
    Тест для получения списка фильтров через "/filters".
    """
    response = client.get("/filters")
    assert response.status_code == 200
    assert isinstance(response.json(), list)  # Проверяем, что возвращается список
    assert len(response.json()) > 0  # Убеждаемся, что список не пустой

def test_apply_filter():
    """
    Тест для применения фильтра через "/apply-filter".
    """
    # Эмуляция загрузки изображения
    image = (np.zeros((100, 100, 3), dtype=np.uint8) * 255).astype(np.uint8)
    _, image_bytes = cv2.imencode(".jpg", image)

    files = {"file": ("test_image.jpg", image_bytes.tobytes(), "image/jpeg")}
    upload_response = client.put("/upload-image", files=files)
    assert upload_response.status_code == 200
    img_db_id = upload_response.headers.get("imgDB_ID")

    # Применение фильтра
    filter_request = {
        "image_id": int(img_db_id),
        "filter_type": "GaussianBlurFilter",
        "filter_params": {"Kernel Size": 5, "Sigma": 1.5}
    }
    response = client.post("/apply-filter", json=filter_request)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
