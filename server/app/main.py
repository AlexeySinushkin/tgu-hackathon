import os

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
from handler.NeuroImageHandler import NeuroImageHandler
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
    img: str  # base64-кодированное изображение или URL
    x_top_left: int
    y_top_left: int

class GPSRequest(BaseModel):
    gps_id: int
    latitude: float
    longitude: float
    date: date

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
    db_handler = database.DatabaseCRUD()
    db_response = db_handler.test_connection()
    return db_response

@app.post("/push_coordinate", summary="Загрузка данных GPS", description="Возвращает ID в DB")
async def db_push_coordinate(request : GPSUpload):
    latitude = request.latitude
    longitude = request.longitude
    app_date = request.date
    db_handler = database.DatabaseCRUD()
    db_id = db_handler.create_data(latitude, longitude, app_date)
    return db_id

@app.get("/db-fetch", summary="Запрашиваем данные с DB", description="Возвращает ID, Latitude, Longitude, Date")
async def db_fetch_coordinate(db_id: int):
    db_handler = database.DatabaseCRUD()
    db_response = db_handler.read_data(db_id)
    return db_response

@app.post("/update_coordinate", summary="Обновляем данных GPS", description="Возвращает True или False.")
async def db_update_coordinate(request : GPSRequest):
    latitude = request.latitude
    longitude = request.longitude
    app_date = request.date
    gps_id = request.gps_id
    db_handler = database.DatabaseCRUD()
    db_response = db_handler.update_data(gps_id, latitude, longitude, app_date)
    return db_response

@app.post("/db-delete", summary="Удаляем данные из DB по ID", description="Возвращает True или False.")
async def db_delete_coordinate(db_id: int):
    db_handler = database.DatabaseCRUD()
    db_response = db_handler.delete_date(db_id)
    return db_response

@app.get("/db-fetch-all-id", summary="Запрашиваем все ID с данными", description="Возвращает словарь ID")
async def db_fetch_id_coordinate():
    db_handler = database.DatabaseCRUD()
    db_ids = db_handler.get_all_ids()
    return db_ids

@app.get("/db-fetch-only-id", summary="Запрашиваем все ID", description="Возвращает словарь ID, Latitude, Longitude, Date")
async def db_fetch_only_id_coordinate():
    db_handler = database.DatabaseCRUD()
    db_ids = db_handler.get_only_ids()
    return db_ids

@app.put("/upload-image", summary="Загрузка фото в DB", description="Загружает фото и возвращает ID с DB.") #PUT используется для создания или обновления ресурса на сервере
async def upload_gps_data(
    latitude: int = Form(...),
    longitude: int = Form(...),
    date: date = Form(...),
    img: UploadFile = File(...),
    x_top_left: int = Form(...),
    y_top_left: int = Form(...)
):
    logger = SingletonLogger().get_logger()
    logger.info(f"/upload-image request {img.filename}")

    # Читаем содержимое загруженного файла
    contents = await img.read()


    logger.info("Object detected")
    image_db = database.ImageDatabaseCRUD()

    # Конвертируем байты в изображение OpenCV
    np_arr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    img_width = image.shape[1]
    img_height = image.shape[0]
    #image_id = image_db.create_image(img.filename, image, json.dumps(json_serializable_boxes))
    image_id = image_db.create_image(filename=img.filename, image=image, latitude=latitude,
                                     longitude=longitude, date=date, width=img_width, height=img_height,
                                     x_top_left=x_top_left, y_top_left=y_top_left)


    # # Сохраняем изображение в базу данных
    # image_id = image_db.create_image(img.filename, image, json.dumps(json_serializable_boxes))
    # if image_id is None:
    #     logger.error("Failed to save image")
    #     return JSONResponse(content={"error": "Failed to save image to database"}, status_code=500)
    # logger.info(f"Boxes: {json.dumps(json_serializable_boxes)}")  # Логируем красиво
    #
    # return JSONResponse(
    #     content={"boxes": json_serializable_boxes},
    #     headers={"imgDB_ID": str(image_id)}
    # )
    return image_id