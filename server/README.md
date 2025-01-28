# Python GPS Server

## About
Программа на Python, которая является backend сервером. В данной программе можно загружать данные GPS в DB и потом работать с этими данными.

## Warning

Если не используем Docker необходимо сделать DB и внести данные utility/database.py
## Installation

Для установки в Windows (Poweshell):
```
git clone https://gitlab.com/slimfy1/pythonprojectback.git
cd pythonprojectback
python -m venv .venv
.venv/Scripts/Activate.ps1
pip install -r requrements.txt
python -m uvicorn app.main:app --reload 
```

Для установки в Linux:
```
git clone https://gitlab.com/slimfy1/pythonprojectback.git
cd pythonprojectback
python -m venv .venv
source .venv/bin/activate
pip install -r requrements.txt
python -m uvicorn app.main:app --reload 
```

Для установки в Docker:
```
docker compose up --build
```
После установки будет доступ к backend по адресу:
http://localhost:8000/docs