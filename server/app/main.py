import os
import base64
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException, Body, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import cv2
import io
from pydantic import BaseModel
from datetime import date  # Импортируем date
from starlette.responses import JSONResponse

import utility.database as database
#import handler.imageProcessor as imgProc
from utility.utility import SingletonLogger, LogExecutionTime
#from handler.NeuroImageHandler import NeuroImageHandler
import json


app = FastAPI(
    title="Image Processing API",
    description="API для загрузки изображений, применения фильтров и работы с базой данных изображений.",
    version="1.0.0",
    contact={
        "name": " Гусаченко А.И.",
        "email": "slimfy1@gmail.com",
    },
    license_info={
        "name": "MIT License",
    },
)
class GPSUpload(BaseModel):
    latitude: float
    longitude: float
    date: date
    img: str
    x_top_left: int
    y_top_left: int

class GPSRequest(BaseModel):
    gps_id: int
    latitude: float
    longitude: float
    date: date


# Создаем модель данных для запроса
class UpdateStatusRequest(BaseModel):
    photo_id: int # ID фотографии
    new_status: bool  # Ожидаемое булево значение

# Настройки CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Укажите здесь нужные домены или оставьте "*" для разрешения всех
    allow_credentials=True,
    allow_methods=["*"],  # Разрешите все методы (GET, POST, PUT и т.д.)
    allow_headers=["*"],  # Разрешите все заголовки
    expose_headers=["imgDB_ID"],  # Укажите, какие заголовки клиент сможет видеть
)

#TODO(Andry): сделал небольшой рефактор и проверить везде ли есть обработка ошибок
@app.get("/")
async def root():
    return {"message": "Hello World"}
@app.get("/info", summary="Информация о сервере.", description="Возвращает данные о сервере.")
async def server_info():
    return {
        "serverName": "GPSServer",
        "serverVersion": "0.0.0"
    }
@app.get("/db-test", summary="Информация о доступности DB", description="Возвращает True или False.")
async def db_test_connection():
    db_handler = database.ImageDatabaseCRUD()
    db_response = db_handler.test_connection()
    return db_response


@app.post("/upload-gps-data/")
async def upload_gps_data(gps_data: GPSUpload):
    logger = SingletonLogger().get_logger()
    logger.info(f"/upload-gps-data request received")

    # Декодирование Base64 в байты
    try:
        img_bytes = base64.b64decode(gps_data.img)
    except base64.binascii.Error:
        raise HTTPException(status_code=400, detail="Invalid Base64 encoding")

    # Конвертируем байты в изображение OpenCV
    np_arr = np.frombuffer(img_bytes, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if image is None:
        raise HTTPException(status_code=400, detail="Invalid image format")

    img_width = image.shape[1]
    img_height = image.shape[0]

    logger.info("Object detected")
    image_db = database.ImageDatabaseCRUD()

    # Сохранение изображения в БД
    image_id = image_db.create_image(
        filename="uploaded_image.jpg",
        image=image,
        latitude=gps_data.latitude,
        longitude=gps_data.longitude,
        date=gps_data.date,
        width=img_width,
        height=img_height,
        x_top_left=gps_data.x_top_left,
        y_top_left=gps_data.y_top_left
    )

    return {"image_id": image_id}

@app.get("/get-unchecked-image", summary="Получить самую старую непроверенную фотографию", description="Получает фото где необходимо проверить наличие ям.") #PUT используется для создания или обновления ресурса на сервере
async def get_unchecked_photo():
    logger = SingletonLogger().get_logger()
    db_handler = database.ImageDatabaseCRUD()
    db_ids = db_handler.get_unchecked_photo_id()

    if not db_ids:
        return JSONResponse(content={}, status_code=204)  # Возвращаем пустой JSON с кодом 204

    min_id = min(db_ids)
    logger.debug(f"Min ID: {min_id}")
    image_data = db_handler.read_image(min_id)  # Получаем (filename, numpy.ndarray)

    if not isinstance(image_data, tuple) or len(image_data) != 2:
        raise ValueError("Ошибка: read_image() вернул неожиданный формат данных")

    filename, last_photo = image_data  # Разбираем кортеж

    if last_photo is None:
        raise ValueError("Ошибка: изображение не найдено в базе данных.")

    if not isinstance(last_photo, np.ndarray):
        raise TypeError(f"Ошибка: ожидается numpy.ndarray, но получен {type(last_photo)}")

    # Преобразуем изображение в uint8 (если необходимо)
    if last_photo.dtype != np.uint8:
        last_photo = last_photo.astype(np.uint8)

    # Кодируем в JPEG
    success, encoded_image = cv2.imencode('.jpg', last_photo)
    if not success:
        raise RuntimeError("Ошибка при кодировании изображения в JPEG")

    # Создаем новый буфер и записываем туда изображение
    image_bytes = io.BytesIO()
    image_bytes.write(encoded_image.tobytes())  # Записываем байты
    image_bytes.seek(0)  # Перемещаем курсор в начало

    headers = {"ImageID": str(min_id)}
    return StreamingResponse(image_bytes, media_type="image/jpeg", headers=headers)

@app.get("/get-confirmed-coordinates", summary="Получить все проверенные координаты", description="Получает все координаты где status = true") #PUT используется для создания или обновления ресурса на сервере
async def get_confirmed_coordinates():
    db_handler = database.ImageDatabaseCRUD()
    db_ids = db_handler.get_confirmed_coordinates()
    return db_ids

@app.get("/get-unconfirmed-coordinates", summary="Получить все ID, где status=false", description="Получить все ID, где status=false") #PUT используется для создания или обновления ресурса на сервере
async def get_confirmed_coordinates():
    db_handler = database.ImageDatabaseCRUD()
    db_ids = db_handler.get_unchecked_photo_id()
    return db_ids

@app.put("/update-status", summary="Обновление статуса фотографий", description="Обновляет статусы в DB.") #PUT используется для создания или обновления ресурса на сервере
async def update_photo_status(request: UpdateStatusRequest):
    new_status = request.new_status
    photo_id = request.photo_id
    db_handler = database.ImageDatabaseCRUD()
    if new_status:
        db_handler.update_status_true(photo_id)
        return_status = True
    else:
        db_handler.delete_image(photo_id)
        return_status = True

    return return_status