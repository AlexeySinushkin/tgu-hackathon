import requests
import time
from Service.handler.NeuroImageHandler import NeuroImageHandler
from utility.utility import SingletonLogger, LogExecutionTime

base_url = "http://176.119.158.23:8001"  # URL сервера
CONFIDENCE_THRESHOLD = 0.6  # Порог уверенности для обнаруженных объектов


@LogExecutionTime()
class DatabaseWorker:
    def __init__(self, url):
        self.url = url

    def test_connection(self):
        logging = SingletonLogger().get_logger()
        logging.info("Testing connection to the database")
        try:
            logging.info("Sending request to the server")
            response = requests.get(self.url + "/db-test")
            return response.text
        except requests.exceptions.RequestException as e:
            logging.error(e)
            print(e)

    def get_image(self):
        logging = SingletonLogger().get_logger()
        try:
            logging.info("Sending request to the server")
            response = requests.get(self.url + "/get-unchecked-image")
            if response.status_code == 204:
                return None
            elif response.status_code == 200:
                return response
        except requests.exceptions.RequestException as e:
            logging.error(e)
            print(e)

    def update_status(self, photo_id: int, status: bool):
        logging = SingletonLogger().get_logger()
        try:
            logging.info("Sending request to update image status")
            response = requests.put(self.url + "/update-status", json={"photo_id": photo_id, "new_status": status})
            return response.text
        except requests.exceptions.RequestException as e:
            logging.error(e)
            print(e)

    def delete_image(self, photo_id: int):
        logging = SingletonLogger().get_logger()
        try:
            logging.info(f"Sending request to delete image with ID: {photo_id}")
            response = requests.delete(self.url + "/delete-image", json={"photo_id": photo_id})
            return response.text
        except requests.exceptions.RequestException as e:
            logging.error(e)
            print(e)


if __name__ == "__main__":
    while True:
        logging = SingletonLogger().get_logger()
        database_handler = DatabaseWorker(base_url)

        server_response = database_handler.get_image()
        logging.debug(f"Server response: {server_response}")

        if server_response is not None:
            photo_id = server_response.headers.get("imageid")
            handler = NeuroImageHandler()
            boxes, confidences = handler.process_image(server_response.content)  # Обновлено для получения уверенности

            logging.debug(f"Boxes: {boxes}, Confidences: {confidences}")

            if boxes is None or all(conf < CONFIDENCE_THRESHOLD for conf in confidences):
                logging.info("No objects detected or confidence below threshold")
                database_handler.update_status(photo_id=photo_id, status=False)
                database_handler.delete_image(photo_id)  # Удаляем изображение
            else:
                logging.info("Objects detected with sufficient confidence")
                database_handler.update_status(photo_id=photo_id, status=True)
                # Здесь можно вернуть данные или обработать их дальше

        else:
            logging.info("No image to process")

        time.sleep(10)  # 10 сек