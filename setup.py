#!/usr/bin/env python3
"""
Script de Setup Automatizado para Filsync
==========================================
Este script te guía en la configuración inicial del proyecto.

Uso:
    python setup.py
"""

import os
import sys
import platform
import subprocess
from pathlib import Path


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_warning(text):
    print(f"{Colors.WARNING}⚠  {text}{Colors.ENDC}")


def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text):
    print(f"{Colors.CYAN}ℹ  {text}{Colors.ENDC}")


def check_python_version():
    """Verifica la versión de Python"""
    print_info("Verificando versión de Python...")
    version = sys.version_info

    if version.major >= 3 and version.minor >= 9:
        print_success(f"Python {version.major}.{version.minor}.{version.micro} ✓")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor}.{version.micro} - Se requiere 3.9 o superior")
        return False


def check_pip():
    """Verifica que pip esté instalado"""
    print_info("Verificando pip...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"],
                       capture_output=True, check=True)
        print_success("pip instalado ✓")
        return True
    except:
        print_error("pip no encontrado")
        return False


def install_requirements():
    """Instala las dependencias"""
    print_info("Instalando dependencias...")

    requirements = [
        'Flask==3.0.0',
        'Flask-SocketIO==5.3.5',
        'Flask-CORS==4.0.0',
        'python-socketio==5.10.0',
        'pyserial==3.5',
        'requests==2.31.0',
        'python-dotenv==1.0.0',
        'eventlet==0.33.3'
    ]

    try:
        for req in requirements:
            print(f"   Instalando {req}...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", req],
                           check=True)
        print_success("Todas las dependencias instaladas ✓")
        return True
    except Exception as e:
        print_error(f"Error instalando dependencias: {e}")
        return False


def create_env_file():
    """Crea el archivo .env para el gateway"""
    print_info("Configurando archivo .env para el gateway local...")

    env_path = Path('.env')

    if env_path.exists():
        response = input(f"{Colors.WARNING}El archivo .env ya existe. ¿Sobreescribir? (s/N): {Colors.ENDC}")
        if response.lower() != 's':
            print_info("Manteniendo archivo .env existente")
            return True

    print("\n" + Colors.BOLD + "Configuración del Gateway Local" + Colors.ENDC)
    print("=" * 60)

    # URL del servidor cloud
    print(f"\n{Colors.CYAN}1. URL del Servidor Cloud{Colors.ENDC}")
    print("   Ejemplos:")
    print("   - https://tu-app.onrender.com")
    print("   - https://tu-app.up.railway.app")
    print("   - http://localhost:8000 (para pruebas locales)")
    cloud_url = input(f"\n{Colors.BOLD}URL del servidor cloud: {Colors.ENDC}").strip()

    if not cloud_url:
        cloud_url = "http://localhost:8000"
        print_warning(f"Usando por defecto: {cloud_url}")

    # Clave secreta
    print(f"\n{Colors.CYAN}2. Clave Secreta del Gateway{Colors.ENDC}")
    print("   Esta clave debe ser la MISMA en el servidor cloud")
    print("   Debe ser difícil de adivinar (mínimo 20 caracteres)")
    gateway_secret = input(f"\n{Colors.BOLD}Clave secreta: {Colors.ENDC}").strip()

    if not gateway_secret:
        import secrets
        gateway_secret = secrets.token_urlsafe(32)
        print_warning(f"Generando clave aleatoria: {gateway_secret}")
        print_warning("¡Guarda esta clave! La necesitarás en el servidor cloud")

    # Gateway ID
    print(f"\n{Colors.CYAN}3. ID del Gateway{Colors.ENDC}")
    print("   Identificador único para este gateway")
    gateway_id = input(f"\n{Colors.BOLD}Gateway ID (default: gateway-001): {Colors.ENDC}").strip()

    if not gateway_id:
        gateway_id = "gateway-001"

    # Tipo de Bluetooth
    print(f"\n{Colors.CYAN}4. Tipo de Bluetooth{Colors.ENDC}")
    print("   SPP = Bluetooth Classic (más común)")
    print("   BLE = Bluetooth Low Energy")
    bt_type = input(f"\n{Colors.BOLD}Tipo (SPP/BLE) [SPP]: {Colors.ENDC}").strip().upper()

    if bt_type not in ['SPP', 'BLE']:
        bt_type = 'SPP'

    # Puerto Bluetooth
    print(f"\n{Colors.CYAN}5. Puerto Bluetooth{Colors.ENDC}")

    system = platform.system()
    if system == "Windows":
        print("   En Windows, busca el puerto COM en:")
        print("   Settings → Bluetooth → Devices → More options")
        default_port = "COM5"
    elif system == "Linux":
        print("   En Linux, típicamente: /dev/rfcomm0")
        default_port = "/dev/rfcomm0"
    elif system == "Darwin":  # macOS
        print("   En macOS, busca: /dev/cu.ESP32-SerialPort")
        default_port = "/dev/cu.ESP32-SerialPort"
    else:
        default_port = "COM5"

    bt_port = input(f"\n{Colors.BOLD}Puerto Bluetooth [{default_port}]: {Colors.ENDC}").strip()

    if not bt_port:
        bt_port = default_port

    # Crear archivo .env
    env_content = f"""# Configuración del Gateway Bluetooth Local
# Generado automáticamente por setup.py

# URL del servidor cloud
CLOUD_SERVER_URL={cloud_url}

# Clave secreta (debe ser la misma que en el servidor cloud)
GATEWAY_SECRET_KEY={gateway_secret}

# ID único de este gateway
GATEWAY_ID={gateway_id}

# Configuración Bluetooth
BLUETOOTH_TYPE={bt_type}
BLUETOOTH_PORT={bt_port}

# Si usas BLE, configura también:
# BLE_DEVICE_NAME=Filsync-ESP32
# BLE_SERVICE_UUID=tu-service-uuid
# BLE_CHAR_UUID=tu-characteristic-uuid
"""

    with open('.env', 'w') as f:
        f.write(env_content)

    print_success("Archivo .env creado exitosamente ✓")

    # Mostrar resumen
    print(f"\n{Colors.BOLD}Resumen de la configuración:{Colors.ENDC}")
    print(f"  Servidor Cloud: {cloud_url}")
    print(f"  Gateway ID: {gateway_id}")
    print(f"  Bluetooth: {bt_type} en {bt_port}")

    if cloud_url.startswith('http://localhost'):
        print_warning("\nEstás usando localhost - perfecto para pruebas locales")
    else:
        print_info("\nRecuerda configurar las mismas variables en tu servidor cloud:")
        print(f"  GATEWAY_SECRET_KEY={gateway_secret}")

    return True


def test_bluetooth_handler():
    """Verifica que el bluetooth_handler esté presente"""
    print_info("Verificando módulo bluetooth_handler...")

    if Path('bluetooth_handler.py').exists():
        print_success("bluetooth_handler.py encontrado ✓")
        return True
    else:
        print_error("bluetooth_handler.py no encontrado")
        print_warning("Copia bluetooth_handler.py de tu proyecto original")
        return False


def show_next_steps():
    """Muestra los siguientes pasos"""
    print_header("¡Configuración Completa!")

    print(f"{Colors.GREEN}{Colors.BOLD}Próximos Pasos:{Colors.ENDC}\n")

    print("1️⃣  Deploy del Servidor Cloud")
    print("   Ver guías en: deployment_guides/")
    print("   - Render: deployment_guides/RENDER_DEPLOYMENT.md")
    print("   - Railway: deployment_guides/RAILWAY_DEPLOYMENT.md\n")

    print("2️⃣  Configurar Variables en el Cloud")
    print("   Asegúrate de agregar:")
    print("   - SECRET_KEY")
    print("   - GATEWAY_SECRET_KEY (la misma que local)")
    print("   - OPENROUTER_API_KEY (opcional)\n")

    print("3️⃣  Ejecutar el Gateway Local")
    print("   python bluetooth_gateway.py\n")

    print("4️⃣  Acceder a la Aplicación")
    print("   Abre tu navegador en la URL del servidor cloud\n")

    print(f"{Colors.CYAN}📚 Documentación completa: README.md{Colors.ENDC}")
    print(f"{Colors.CYAN}🆘 ¿Problemas? Revisa las guías de troubleshooting{Colors.ENDC}\n")


def main():
    """Función principal del setup"""
    print_header("FILSYNC - Setup Automatizado")

    print(f"{Colors.CYAN}Este script te ayudará a configurar Filsync paso a paso.{Colors.ENDC}\n")

    # Verificaciones
    checks = [
        ("Python 3.9+", check_python_version),
        ("pip", check_pip),
    ]

    for name, check_func in checks:
        if not check_func():
            print_error(f"\n✗ Setup fallido: {name} no cumple requisitos")
            sys.exit(1)

    # Instalar dependencias
    print()
    if not install_requirements():
        print_error("\n✗ Setup fallido: Error instalando dependencias")
        sys.exit(1)

    # Verificar bluetooth_handler
    print()
    test_bluetooth_handler()

    # Crear archivo .env
    print()
    if not create_env_file():
        print_error("\n✗ Setup fallido: Error creando .env")
        sys.exit(1)

    # Mostrar siguientes pasos
    print()
    show_next_steps()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Setup cancelado por el usuario{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.FAIL}Error inesperado: {e}{Colors.ENDC}")
        sys.exit(1)