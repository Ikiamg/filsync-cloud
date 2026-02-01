"""
Gateway Bluetooth Local para Filsync
=====================================
Este script se ejecuta en tu computadora local y:
1. Se conecta al ESP32 vía Bluetooth
2. Envía los datos al servidor cloud en tiempo real
3. Es muy ligero (solo maneja la conexión BT)

Uso:
    python bluetooth_gateway.py
"""

import asyncio
import logging
import sys
import time
import os
import json
import requests
import threading
from datetime import datetime
from dotenv import load_dotenv

# Importar el manejador de Bluetooth original
try:
    from bluetooth_handler import BluetoothHandler
except ImportError:
    print("❌ Error: No se encontró bluetooth_handler.py")
    print("   Asegúrate de ejecutar este script en el mismo directorio que bluetooth_handler.py")
    sys.exit(1)

load_dotenv()

# Configuración
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('gateway.log')
    ]
)
logger = logging.getLogger(__name__)


class CloudGateway:
    """Gateway que conecta Bluetooth local con servidor cloud"""

    def __init__(self):
        self.cloud_url = os.getenv('CLOUD_SERVER_URL', 'http://localhost:8000')
        self.secret_key = os.getenv('GATEWAY_SECRET_KEY', 'default-secret-change-me')
        self.gateway_id = os.getenv('GATEWAY_ID', 'gateway-001')

        # Estado
        self.connected_to_cloud = False
        self.last_ping = 0
        self.reconnect_attempts = 0

        # Bluetooth
        self.bluetooth_handler = None

        # Cola de datos
        self.data_queue = []
        self.queue_lock = threading.Lock()

    def on_bluetooth_data(self, data):
        """Callback cuando llegan datos del Bluetooth"""
        try:
            # Agregar timestamp y gateway_id
            data['gateway_id'] = self.gateway_id
            data['received_at'] = datetime.now().isoformat()

            # Agregar a cola
            with self.queue_lock:
                self.data_queue.append(data)

            # Enviar inmediatamente si está conectado
            if self.connected_to_cloud:
                self._send_data_to_cloud(data)

        except Exception as e:
            logger.error(f"Error procesando datos Bluetooth: {e}")

    def _send_data_to_cloud(self, data):
        """Envía datos al servidor cloud"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'X-Gateway-Secret': self.secret_key
            }

            response = requests.post(
                f"{self.cloud_url}/api/gateway/data",
                json=data,
                headers=headers,
                timeout=5
            )

            if response.status_code == 200:
                # Remover de cola si se envió exitosamente
                with self.queue_lock:
                    if data in self.data_queue:
                        self.data_queue.remove(data)

                self.connected_to_cloud = True
                self.reconnect_attempts = 0
                return True
            else:
                logger.warning(f"Cloud respondió con código: {response.status_code}")
                return False

        except requests.exceptions.ConnectionError:
            if self.connected_to_cloud:
                logger.error("❌ Conexión perdida con el servidor cloud")
            self.connected_to_cloud = False
            return False

        except Exception as e:
            logger.error(f"Error enviando datos al cloud: {e}")
            return False

    def _flush_queue(self):
        """Intenta enviar datos pendientes en la cola"""
        if not self.connected_to_cloud:
            return

        with self.queue_lock:
            queue_copy = self.data_queue.copy()

        for data in queue_copy:
            if self._send_data_to_cloud(data):
                logger.info(f"✓ Dato pendiente enviado al cloud")

    def _register_gateway(self):
        """Registra este gateway en el servidor cloud"""
        try:
            headers = {
                'Content-Type': 'application/json',
                'X-Gateway-Secret': self.secret_key
            }

            payload = {
                'gateway_id': self.gateway_id,
                'bluetooth_type': os.getenv('BLUETOOTH_TYPE', 'SPP'),
                'device_name': os.getenv('BLE_DEVICE_NAME', 'Filsync-ESP32'),
                'registered_at': datetime.now().isoformat()
            }

            response = requests.post(
                f"{self.cloud_url}/api/gateway/register",
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                logger.info("✓ Gateway registrado en el servidor cloud")
                self.connected_to_cloud = True
                return True
            else:
                logger.error(f"Error registrando gateway: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error conectando al cloud: {e}")
            return False

    def _ping_cloud(self):
        """Envía ping periódico al servidor cloud"""
        while True:
            try:
                time.sleep(30)  # Ping cada 30 segundos

                if not self.connected_to_cloud:
                    # Intentar reconectar
                    if self._register_gateway():
                        logger.info("✓ Reconectado al servidor cloud")
                        self._flush_queue()  # Enviar datos pendientes
                    continue

                # Enviar ping
                headers = {'X-Gateway-Secret': self.secret_key}
                response = requests.get(
                    f"{self.cloud_url}/api/gateway/ping",
                    headers=headers,
                    params={'gateway_id': self.gateway_id},
                    timeout=5
                )

                if response.status_code != 200:
                    self.connected_to_cloud = False
                    logger.warning("Ping falló, marcando como desconectado")
                else:
                    self.last_ping = time.time()

            except Exception as e:
                self.connected_to_cloud = False
                logger.debug(f"Error en ping: {e}")

    def start(self):
        """Inicia el gateway"""
        logger.info("=" * 60)
        logger.info("  FILSYNC BLUETOOTH GATEWAY")
        logger.info("  Conectando ESP32 local con servidor cloud")
        logger.info("=" * 60)
        logger.info(f"\n📡 Servidor Cloud: {self.cloud_url}")
        logger.info(f"🔑 Gateway ID: {self.gateway_id}")
        logger.info(f"🔵 Bluetooth Type: {os.getenv('BLUETOOTH_TYPE', 'SPP')}\n")

        # Registrar en cloud
        logger.info("🌐 Conectando al servidor cloud...")
        if self._register_gateway():
            logger.info("✓ Conexión establecida con el cloud")
        else:
            logger.warning("⚠️  No se pudo conectar al cloud (se reintentará automáticamente)")
            logger.warning("    El gateway funcionará en modo offline y sincronizará cuando sea posible")

        # Iniciar Bluetooth
        logger.info("\n📱 Iniciando conexión Bluetooth...")
        try:
            self.bluetooth_handler = BluetoothHandler(data_callback=self.on_bluetooth_data)
            self.bluetooth_handler.start()
            logger.info("✓ Bluetooth iniciado correctamente")
        except Exception as e:
            logger.error(f"❌ Error iniciando Bluetooth: {e}")
            return

        # Iniciar hilo de ping
        ping_thread = threading.Thread(target=self._ping_cloud, daemon=True)
        ping_thread.start()

        logger.info("\n" + "=" * 60)
        logger.info("🚀 GATEWAY EN EJECUCIÓN")
        logger.info("=" * 60)
        logger.info("Presiona Ctrl+C para detener\n")

        # Mantener ejecutando
        try:
            while True:
                time.sleep(1)

                # Mostrar estado cada 60 segundos
                if int(time.time()) % 60 == 0:
                    status = "🟢 CONECTADO" if self.connected_to_cloud else "🔴 DESCONECTADO"
                    bt_status = "🟢 CONECTADO" if self.bluetooth_handler.connected else "🔴 DESCONECTADO"

                    with self.queue_lock:
                        queue_size = len(self.data_queue)

                    logger.info(
                        f"\n📊 Estado: Cloud {status} | Bluetooth {bt_status} | Cola: {queue_size} datos pendientes")

        except KeyboardInterrupt:
            logger.info("\n\n⏹️  Deteniendo gateway...")
            if self.bluetooth_handler:
                self.bluetooth_handler.stop()
            logger.info("✓ Gateway detenido\n")


def main():
    """Función principal"""
    # Verificar variables de entorno
    required_vars = ['CLOUD_SERVER_URL', 'GATEWAY_SECRET_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        logger.error("❌ Error: Variables de entorno faltantes:")
        for var in missing_vars:
            logger.error(f"   - {var}")
        logger.error("\nCrea un archivo .env con:")
        logger.error("CLOUD_SERVER_URL=https://tu-app.render.com")
        logger.error("GATEWAY_SECRET_KEY=tu_clave_secreta")
        logger.error("BLUETOOTH_TYPE=SPP")
        logger.error("BLUETOOTH_PORT=COM5")
        sys.exit(1)

    # Iniciar gateway
    gateway = CloudGateway()
    gateway.start()


if __name__ == '__main__':
    main()