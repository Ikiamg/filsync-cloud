import threading
import time
import logging
import re
from datetime import datetime
from Filsync2.cloud_server.config import Config

# Importaciones condicionales según el tipo de Bluetooth
try:
    import serial

    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

try:
    from bleak import BleakClient, BleakScanner
    import asyncio

    BLEAK_AVAILABLE = True
except ImportError:
    BLEAK_AVAILABLE = False

logger = logging.getLogger(__name__)


class BiometricData:
    """Clase para almacenar datos biométricos"""

    def __init__(self):
        self.fc = 0
        self.spo2 = 0
        self.temp = 0.0
        self.state = "SIN_DEDO"
        self.ir = 0
        self.timestamp = datetime.now().timestamp()
        self.lock = threading.Lock()

        # Buffers para gráficas
        self.fc_buffer = []
        self.spo2_buffer = []
        self.temp_buffer = []
        self.timestamps = []

    def update(self, key, value):
        """Actualiza un valor y su buffer"""
        with self.lock:
            if key == 'FC':
                self.fc = int(value)
                self._add_to_buffer(self.fc_buffer, self.fc)
            elif key == 'SpO2':
                self.spo2 = int(value)
                self._add_to_buffer(self.spo2_buffer, self.spo2)
            elif key == 'Temp':
                self.temp = float(value)
                self._add_to_buffer(self.temp_buffer, self.temp)
            elif key == 'STATE':
                self.state = value
            elif key == 'IR':
                self.ir = int(value)

            self.timestamp = datetime.now().timestamp()

            # Inferir estado si no viene del ESP32 (Opción B)
            if key in ['FC', 'SpO2'] and self.state == "SIN_DEDO":
                self._infer_state()

    def _add_to_buffer(self, buffer, value):
        """Añade valor al buffer y mantiene el tamaño máximo"""
        buffer.append(value)
        if len(buffer) > Config.MAX_DATA_POINTS:
            buffer.pop(0)

        # Sincronizar timestamps
        self.timestamps.append(datetime.now().strftime('%H:%M:%S'))
        if len(self.timestamps) > Config.MAX_DATA_POINTS:
            self.timestamps.pop(0)

    def _infer_state(self):
        """Inferir estado basado en FC (Opción B - fallback)"""
        if self.fc == 0:
            self.state = "SIN_DEDO"
        elif self.fc < 65:
            self.state = "RELAX"
        elif 65 <= self.fc <= 80:
            self.state = "NORMAL"
        else:
            self.state = "STRESS"

    def get_dict(self):
        """Retorna datos como diccionario"""
        with self.lock:
            return {
                'fc': self.fc,
                'spo2': self.spo2,
                'temp': round(self.temp, 2),
                'state': self.state,
                'ir': self.ir,
                'timestamp': self.timestamp,
                'buffers': {
                    'fc': self.fc_buffer.copy(),
                    'spo2': self.spo2_buffer.copy(),
                    'temp': [round(t, 2) for t in self.temp_buffer],
                    'timestamps': self.timestamps.copy()
                }
            }


class BluetoothHandler:
    """Manejador de conexión Bluetooth (SPP o BLE)"""

    def __init__(self, data_callback=None):
        self.data = BiometricData()
        self.data_callback = data_callback
        self.running = False
        self.connected = False
        self.connection = None
        self.thread = None

        # Patrones de regex para parsear datos
        self.patterns = {
            'FC': re.compile(r'FC:(\d+)'),
            'SpO2': re.compile(r'SpO2:(\d+)'),
            'Temp': re.compile(r'Temp:([\d.]+)'),
            'STATE': re.compile(r'STATE:(RELAX|NORMAL|STRESS|SIN_DEDO)'),
            'IR': re.compile(r'IR:(\d+)')
        }

    def start(self):
        """Inicia el hilo de lectura Bluetooth"""
        if self.running:
            logger.warning("Bluetooth ya está ejecutándose")
            return

        self.running = True

        if Config.BLUETOOTH_TYPE == 'SPP':
            self.thread = threading.Thread(target=self._run_spp, daemon=True)
        elif Config.BLUETOOTH_TYPE == 'BLE':
            self.thread = threading.Thread(target=self._run_ble_wrapper, daemon=True)
        else:
            logger.error(f"Tipo de Bluetooth no válido: {Config.BLUETOOTH_TYPE}")
            return

        self.thread.start()
        logger.info(f"Bluetooth iniciado en modo {Config.BLUETOOTH_TYPE}")

    def stop(self):
        """Detiene la conexión Bluetooth"""
        logger.info("Deteniendo Bluetooth...")
        self.running = False

        if self.connection:
            try:
                if Config.BLUETOOTH_TYPE == 'SPP' and hasattr(self.connection, 'close'):
                    self.connection.close()
            except Exception as e:
                logger.error(f"Error al cerrar conexión: {e}")

        self.connected = False

    def _run_spp(self):
        """Ejecuta lectura Bluetooth Classic SPP"""
        if not SERIAL_AVAILABLE:
            logger.error("pyserial no está instalado. Instala con: pip install pyserial")
            return

        while self.running:
            try:
                if not self.connected:
                    logger.info(f"Conectando a {Config.BLUETOOTH_PORT}...")
                    self.connection = serial.Serial(
                        Config.BLUETOOTH_PORT,
                        baudrate=115200,
                        timeout=2
                    )
                    self.connected = True
                    logger.info(f"✓ Conectado a {Config.BLUETOOTH_PORT}")

                # Leer línea del puerto serial
                if self.connection.in_waiting > 0:
                    line = self.connection.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        self._parse_line(line)

                time.sleep(0.05)  # 50ms entre lecturas

            except serial.SerialException as e:
                if self.connected:
                    logger.error(f"Conexión perdida: {e}")
                    self.connected = False

                if self.connection:
                    try:
                        self.connection.close()
                    except:
                        pass
                    self.connection = None

                logger.info("Reintentando conexión en 5 segundos...")
                time.sleep(5)

            except Exception as e:
                logger.error(f"Error inesperado: {e}", exc_info=True)
                time.sleep(5)

    def _run_ble_wrapper(self):
        """Wrapper para ejecutar asyncio en un hilo"""
        if not BLEAK_AVAILABLE:
            logger.error("bleak no está instalado. Instala con: pip install bleak")
            return

        # Crear nuevo event loop para este hilo
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(self._run_ble())
        except Exception as e:
            logger.error(f"Error en BLE: {e}", exc_info=True)
        finally:
            loop.close()

    async def _run_ble(self):
        """Ejecuta lectura Bluetooth Low Energy"""
        while self.running:
            try:
                if not self.connected:
                    logger.info(f"Buscando dispositivo BLE: {Config.BLE_DEVICE_NAME}...")

                    # Escanear dispositivos
                    devices = await BleakScanner.discover(timeout=10.0)
                    device = None

                    for d in devices:
                        if d.name and Config.BLE_DEVICE_NAME in d.name:
                            device = d
                            break

                    if not device:
                        logger.warning(f"No se encontró {Config.BLE_DEVICE_NAME}")
                        await asyncio.sleep(5)
                        continue

                    logger.info(f"Dispositivo encontrado: {device.name} ({device.address})")

                    # Conectar al dispositivo
                    async with BleakClient(device.address) as client:
                        self.connected = True
                        logger.info("✓ Conectado vía BLE")

                        # Si no hay UUIDs configurados, listar servicios
                        if not Config.BLE_CHAR_UUID:
                            logger.info("Servicios disponibles:")
                            for service in client.services:
                                logger.info(f"  Service: {service.uuid}")
                                for char in service.characteristics:
                                    logger.info(f"    Characteristic: {char.uuid} - {char.properties}")

                            logger.error("Configura BLE_SERVICE_UUID y BLE_CHAR_UUID en .env")
                            self.running = False
                            return

                        # Callback para notificaciones
                        def notification_handler(sender, data):
                            try:
                                line = data.decode('utf-8', errors='ignore').strip()
                                if line:
                                    self._parse_line(line)
                            except Exception as e:
                                logger.error(f"Error procesando notificación: {e}")

                        # Suscribirse a notificaciones
                        await client.start_notify(Config.BLE_CHAR_UUID, notification_handler)
                        logger.info("Escuchando notificaciones BLE...")

                        # Mantener conexión
                        while self.running and client.is_connected:
                            await asyncio.sleep(1)

                        await client.stop_notify(Config.BLE_CHAR_UUID)

            except Exception as e:
                logger.error(f"Error BLE: {e}")
                self.connected = False
                await asyncio.sleep(5)

    def _parse_line(self, line):
        """Parsea una línea recibida del ESP32"""
        logger.debug(f"Recibido: {line}")

        # Buscar patrones en la línea
        for key, pattern in self.patterns.items():
            match = pattern.search(line)
            if match:
                value = match.group(1)
                self.data.update(key, value)
                logger.debug(f"  {key} = {value}")

        # Llamar callback si existe
        if self.data_callback:
            try:
                self.data_callback(self.data.get_dict())
            except Exception as e:
                logger.error(f"Error en callback: {e}")

    def get_current_data(self):
        """Retorna los datos actuales"""
        return self.data.get_dict()