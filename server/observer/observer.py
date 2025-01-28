import csv
from datetime import datetime

class AuditObserver:
    def __init__(self, csv_file: str):
        """
        Инициализация AuditObserver с указанием файла CSV.
        :param csv_file: Путь к файлу CSV для записи данных.
        """
        self.csv_file = csv_file
        # Проверяем, существует ли файл, если нет - создаём с заголовками
        try:
            with open(self.csv_file, 'x', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(["timestamp", "user", "action", "details"])
        except FileExistsError:
            pass  # Файл уже существует, ничего не делаем

    def notify(self, user: str, action: str, details: dict):
        """
        Записывает событие в CSV файл.
        :param user: Имя пользователя.
        :param action: Выполненное действие.
        :param details: Дополнительные детали (в формате словаря).
        """
        timestamp = datetime.now().isoformat()
        details_str = str(details)
        with open(self.csv_file, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, user, action, details_str])
        print(f"Audit Log written - User: {user}, Action: {action}, Details: {details}")
