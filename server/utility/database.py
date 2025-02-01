import base64

import psycopg2
import cv2
import numpy as np
from utility.utility import SingletonLogger, LogExecutionTime
from observer.observer import AuditObserver
from datetime import date  # Импортируем date
# Параметры подключения к базе данных
import json
conn_params = {
    "dbname": "pyservdb",
    "user": "pyserv",
    "password": "admin",
    "host": "176.119.158.23",  # Указываем имя сервиса из docker-compose.yml
    "port": 5432  # Внутренний порт PostgreSQL
}

class DatabaseConnection:
    """
    Контекстный менеджер для управления подключением к базе данных.
    """
    def __init__(self, db_params=None):
        logger = SingletonLogger().get_logger()
        logger.debug("DatabaseConnection init called")
        self.db_params = db_params or conn_params

    def __enter__(self):
        self.connection = psycopg2.connect(**self.db_params)
        return self.connection

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            self.connection.close()

@LogExecutionTime()
class DatabaseCRUD(DatabaseConnection):
    """
    Класс, реализующий операции CRUD для работы с таблицей изображений.
    """
    def __init__(self, db_params=None, audit_file="audit_log.csv"):
        super().__init__(db_params)
        self.audit_observer = AuditObserver(audit_file)
        self._ensure_database_and_table()

    def _ensure_database_and_table(self):
        """
        Проверяет наличие базы данных и таблицы gps. Если они отсутствуют, создаёт их.
        """
        logger = SingletonLogger().get_logger()
        try:
            # Проверка и создание базы данных
            db_admin_params = {**self.db_params, "dbname": "postgres"}
            with DatabaseConnection(db_admin_params) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (self.db_params["dbname"],))
                    exists = cur.fetchone()
                    if not exists:
                        cur.execute(f"CREATE DATABASE {self.db_params['dbname']};")
                        logger.info(f"Database {self.db_params['dbname']} created.")

            # Проверка и создание таблицы
            with DatabaseConnection(self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS gps (
                            id SERIAL PRIMARY KEY,
                            latitude REAL NOT NULL,
                            longitude REAL NOT NULL,
                            data DATE NOT NULL
                        );
                    """)
                    conn.commit()
                    logger.info("Table 'gps' ensured to exist.")
        except Exception as e:
            logger.error(f"Error ensuring database and table: {e}")

    @LogExecutionTime()
    def test_connection(self) -> bool:
        logger = SingletonLogger().get_logger()
        try:
            with DatabaseConnection(self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
                    result = cur.fetchone()
                    if result and result[0] == 1:
                        logger.info("Database connection test successful.")
                        return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    @LogExecutionTime()
    def create_data(self, latitude_data:int, longitude_data:int, data:date) -> int:
        logger = SingletonLogger().get_logger()
        try:

            with DatabaseConnection(self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO gps (latitude, longitude, data)
                        VALUES (%s, %s, %s)
                        RETURNING id;
                        """,
                        (latitude_data, longitude_data, data)
                    )
                    gps_id = cur.fetchone()[0]
                    conn.commit()
                    logger.info(f"GPS coordinate created with ID: {gps_id}")

                    # Уведомляем AuditObserver
                    self.audit_observer.notify(
                        user="system",
                        action="create_image",
                        details={"id": gps_id}
                    )
                    return gps_id
        except Exception as e:
            logger.error(f"Error creating GPS coordinate: {e}")
            return -1

    @LogExecutionTime()
    def read_data(self, gps_id: int) -> tuple[int, int, date]:
        logger = SingletonLogger().get_logger()
        try:
            with DatabaseConnection(self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT latitude, longitude, data FROM gps WHERE id = %s;
                        """,
                        (gps_id,)
                    )
                    row = cur.fetchone()
                    return row[0], row[1], row[2]
        except Exception as e:
            logger.error(f"Error reading data: {e}")
            return None

    @LogExecutionTime()
    def update_data(self, gps_id: int, latitude_data:int, longitude_data:int, data:date) -> bool:
        logger = SingletonLogger().get_logger()
        try:
            with DatabaseConnection(self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE gps
                        SET latitude = %s, longitude = %s, data = %s
                        WHERE id = %s;
                        """,
                        (latitude_data, longitude_data, data, gps_id)
                    )
                    conn.commit()
                    logger.info(f"Image with ID {gps_id} updated successfully.")
                    return True
        except Exception as e:
            logger.error(f"Error updating image: {e}")
            return False

    @LogExecutionTime()
    def delete_date(self, gps_id: int) -> bool:
        logger = SingletonLogger().get_logger()
        try:
            with DatabaseConnection(self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        DELETE FROM gps
                        WHERE id = %s;
                        """,
                        (gps_id,)
                    )
                    conn.commit()
                    logger.info(f"GPS coordinate with ID {gps_id} deleted successfully.")

                    # Уведомляем AuditObserver
                    self.audit_observer.notify(
                        user="system",
                        action="delete_image",
                        details={"id": gps_id}
                    )
                    return True
        except Exception as e:
            logger.error(f"Error deleting image: {e}")
            return False

    def get_only_ids(self):
        try:
            # Подключение к базе данных
            with DatabaseConnection(self.db_params) as conn:
                with conn.cursor() as cur:
                    # SQL-запрос для получения всех значений столбца id
                    cur.execute("SELECT id FROM gps;")

                    # Получение всех строк результата
                    ids = cur.fetchall()

                    # Преобразование результата в список (каждая строка — это кортеж)
                    ids = [row[0] for row in ids]

                    return ids
        except Exception as e:
            print(f"Error: {e}")
            return []

    def get_all_ids(self):
        try:
            # Подключение к базе данных
            with DatabaseConnection(self.db_params) as conn:
                with conn.cursor() as cur:
                    # SQL-запрос для получения всех данных
                    cur.execute("SELECT id, latitude, longitude, data FROM gps;")

                    # Получение всех строк результата
                    rows = cur.fetchall()

                    # Преобразование результата в список словарей для удобства
                    results = [
                        {
                            'id': row[0],
                            'latitude': row[1],
                            'longitude': row[2],
                            'data': row[3]
                        }
                        for row in rows
                    ]

                    return results
        except Exception as e:
            print(f"Error: {e}")
            return []
@LogExecutionTime()
class ImageDatabaseCRUD(DatabaseConnection):
    """
    Класс, реализующий операции CRUD для работы с таблицей изображений.
    """
    def __init__(self, db_params=None, audit_file="audit_log.csv"):
        super().__init__(db_params)
        self.audit_observer = AuditObserver(audit_file)
        self._ensure_database_and_table()

    def _ensure_database_and_table(self):
        """
        Проверяет наличие базы данных и таблицы neurophotos. Если они отсутствуют, создаёт их.
        """
        logger = SingletonLogger().get_logger()
        try:
            # Проверка и создание базы данных
            db_admin_params = {**self.db_params, "dbname": "postgres"}
            with DatabaseConnection(db_admin_params) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (self.db_params["dbname"],))
                    exists = cur.fetchone()
                    if not exists:
                        cur.execute(f"CREATE DATABASE {self.db_params['dbname']};")
                        logger.info(f"Database {self.db_params['dbname']} created.")

            # Проверка и создание таблицы
            with DatabaseConnection(self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS neurophotos (
                            id SERIAL PRIMARY KEY,
                            filename TEXT NOT NULL,
                            photo BYTEA NOT NULL
                        );
                    """)
                    conn.commit()
                    logger.info("Table 'neurophotos' ensured to exist.")
        except Exception as e:
            logger.error(f"Error ensuring database and table: {e}")

    @LogExecutionTime()
    def test_connection(self) -> bool:
        logger = SingletonLogger().get_logger()
        try:
            with DatabaseConnection(self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1;")
                    result = cur.fetchone()
                    if result and result[0] == 1:
                        logger.info("Database connection test successful.")
                        return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    @LogExecutionTime()
    def create_image(self, filename: str, image: np.ndarray, coords) -> int:
        logger = SingletonLogger().get_logger()
        try:
            _, encoded_image = cv2.imencode('.png', image)
            binary_data = encoded_image.tobytes()

            with DatabaseConnection(self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO neurophotos (filename, photo, coordinate)
                        VALUES (%s, %s, %s::jsonb)
                        RETURNING id;
                        """,
                        (filename, binary_data, json.dumps(coords))  # Преобразуем Python-объект в JSON-строку
                    )
                    image_id = cur.fetchone()[0]
                    conn.commit()
                    logger.info(f"Image created with ID: {image_id}")

                    # Уведомляем AuditObserver
                    self.audit_observer.notify(
                        user="system",
                        action="create_image",
                        details={"id": image_id, "filename": filename}
                    )
                    return image_id
        except Exception as e:
            logger.error(f"Error creating image: {e}")
            return -1

    @LogExecutionTime()
    def read_image(self, image_id: int) -> tuple[str, np.ndarray]:
        logger = SingletonLogger().get_logger()
        try:
            with DatabaseConnection(self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT filename, photo FROM neurophotos WHERE id = %s;
                        """,
                        (image_id,)
                    )
                    row = cur.fetchone()
                    if row:
                        filename, binary_data = row
                        np_array = np.frombuffer(binary_data, np.uint8)
                        image = cv2.imdecode(np_array, cv2.IMREAD_UNCHANGED)
                        return filename, image
                    else:
                        logger.info(f"Image with ID {image_id} not found.")
                        return None
        except Exception as e:
            logger.error(f"Error reading image: {e}")
            return None

    @LogExecutionTime()
    def update_image(self, image_id: int, filename: str, image: np.ndarray) -> bool:
        logger = SingletonLogger().get_logger()
        try:
            _, encoded_image = cv2.imencode('.png', image)
            binary_data = encoded_image.tobytes()

            with DatabaseConnection(self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        UPDATE neurophotos
                        SET filename = %s, photo = %s
                        WHERE id = %s;
                        """,
                        (filename, binary_data, image_id)
                    )
                    conn.commit()
                    logger.info(f"Image with ID {image_id} updated successfully.")
                    return True
        except Exception as e:
            logger.error(f"Error updating image: {e}")
            return False

    @LogExecutionTime()
    def delete_image(self, image_id: int) -> bool:
        logger = SingletonLogger().get_logger()
        try:
            with DatabaseConnection(self.db_params) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        DELETE FROM neurophotos
                        WHERE id = %s;
                        """,
                        (image_id,)
                    )
                    conn.commit()
                    logger.info(f"Image with ID {image_id} deleted successfully.")

                    # Уведомляем AuditObserver
                    self.audit_observer.notify(
                        user="system",
                        action="delete_image",
                        details={"id": image_id}
                    )
                    return True
        except Exception as e:
            logger.error(f"Error deleting image: {e}")
            return False
