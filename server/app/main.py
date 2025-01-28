import os

import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import cv2
import io
from pydantic import BaseModel
from datetime import date  # Импортируем date
from starlette.responses import JSONResponse

import utility.database as database
import handler.imageProcessor as imgProc
from utility.utility import SingletonLogger, LogExecutionTime

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

class GPSRequest(BaseModel):
    gps_id: int
    latitude: int
    longitude: int
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
async def db_push_coordinate(request : GPSRequest):
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