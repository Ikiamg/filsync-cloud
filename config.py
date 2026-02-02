import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # OpenRouter API
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1/chat/completions'

    # Modelo IA (puedes cambiar según necesites)
    AI_MODEL = 'openai/gpt-oss-120b:free'

    # Bluetooth
    BLUETOOTH_TYPE = os.getenv('BLUETOOTH_TYPE', 'SPP')
    BLUETOOTH_PORT = os.getenv('BLUETOOTH_PORT', 'COM6')
    BLE_DEVICE_NAME = os.getenv('BLE_DEVICE_NAME', 'Filsync-ESP32')
    BLE_SERVICE_UUID = os.getenv('BLE_SERVICE_UUID', None)
    BLE_CHAR_UUID = os.getenv('BLE_CHAR_UUID', None)

    # Buffer de datos
    MAX_DATA_POINTS = 100

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'hJpRYahvPJbNHxQzJIsnV1XKtw76MhgG58Y8lJmUQdw')

    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))

