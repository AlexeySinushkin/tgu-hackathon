import requests # Импортируем библиотеку для выполнения HTTP-запросов
import time  # Импортируем библиотеку для работы с временем
from Service.handler.NeuroImageHandler import NeuroImageHandler # Импортируем класс для обработки изображений
from utility.utility import SingletonLogger, LogExecutionTime  # Импортируем логгер и декоратор для измерения времени выполнения

base_url = "http://176.119.158.23:8001"  # URL сервера
CONFIDENCE_THRESHOLD = 0.5  # Порог уверенности для обнаруженных объектов (если ниже, объект считается нераспознанным)


@LogExecutionTime() # Декоратор для измерения времени выполнения класса
class DatabaseWorker:
    def __init__(self, url): # Конструктор класса, инициализирующий URL
        self.url = url # Сохраняем URL в экземпляре класса

    def test_connection(self):
        logging = SingletonLogger().get_logger() # Получаем логгер
         logging.info("Testing connection to the database") # Логируем информацию о тестировании соединения
        try:
            logging.info("Sending request to the server") # Логируем информацию о запросе к серверу
            response = requests.get(self.url + "/db-test")# Отправляем GET-запрос на тестирование соединения
            return response.text  # Возвращаем текст ответа
        except requests.exceptions.RequestException as e: # Обрабатываем возможные исключения при запросе
            logging.error(e) # Логируем ошибку
            print(e)

    def get_image(self):
        logging = SingletonLogger().get_logger() # Получаем логгер
        try:
            logging.info("Sending request to the server") # Логируем информацию о запросе к серверу
            response = requests.get(self.url + "/get-unchecked-image") # Отправляем GET-запрос для получения изображения
            if response.status_code == 204:  # Если статус ответа 204 (Нет содержимого)
                return None # Возвращаем None (изображений нет)
            elif response.status_code == 200: # Если статус ответа 200 (Успешно)
                return response  # Возвращаем ответ 
        except requests.exceptions.RequestException as e: # Обрабатываем возможные исключения при запросе
            logging.error(e) # Логируем ошибку
            print(e)

    def update_status(self, photo_id: int, status: bool):
        logging = SingletonLogger().get_logger()
        try:
            logging.info("Sending request to update image status") # Логируем информацию о запросе на обновление статуса изображения
            response = requests.put(self.url + "/update-status", json={"photo_id": photo_id, "new_status": status}) # Отправляем PUT-запрос для обновления статуса изображения с ID photo_id
            return response.text  # Возвращаем текст ответа
        except requests.exceptions.RequestException as e: # Обрабатываем возможные исключения при запросе
            logging.error(e)
            print(e)

    def delete_image(self, photo_id: int):
        logging = SingletonLogger().get_logger()
        try:
            logging.info(f"Sending request to delete image with ID: {photo_id}")
            response = requests.delete(self.url + "/delete-image", json={"photo_id": photo_id}) # Отправляем DELETE-запрос для удаления изображения с ID photo_id
            return response.text
        except requests.exceptions.RequestException as e:
            logging.error(e)
            print(e)


if __name__ == "__main__": 
    while True:  # Бесконечный цикл для периодической обработки изображений
        logging = SingletonLogger().get_logger()
        database_handler = DatabaseWorker(base_url) # Создаем экземпляр класса DatabaseWorker с базовым URL

        server_response = database_handler.get_image() # Получаем изображение от сервера
        logging.debug(f"Server response: {server_response}") # Логируем ответ сервера

        if server_response is not None:  # Если изображение получено
            photo_id = server_response.headers.get("imageid") # Извлекаем ID изображения из заголовков ответа
            handler = NeuroImageHandler() # Создаем экземпляр обработчика изображений
            boxes, confidences = handler.process_image(server_response.content)  # Обрабатываем изображение и получаем координаты объектов и их уверенность

            logging.debug(f"Boxes: {boxes}, Confidences: {confidences}") # Логируем координаты объектов и их уверенность

            if boxes is None or all(conf < CONFIDENCE_THRESHOLD for conf in confidences):  # Если объекты не обнаружены или их уверенность ниже порога
                logging.info("No objects detected or confidence below threshold")
                database_handler.update_status(photo_id=photo_id, status=False) # Обновляем статус изображения на 'необработано'
                database_handler.delete_image(photo_id)  # Удаляем изображение
            else:
                logging.info("Objects detected with sufficient confidence")
                database_handler.update_status(photo_id=photo_id, status=True) # Обновляем статус изображения на 'обработано'
             

        else:
            logging.info("No image to process") # Логируем, что изображений для обработки нет

        time.sleep(10)  # Задержка в 10 секунд перед следующей итерацией цикла
