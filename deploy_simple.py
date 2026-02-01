#!/usr/bin/env python3
"""
Script de Deployment SIMPLIFICADO para Filsync Cloud
====================================================
Esta versión NO requiere Git instalado.
Te da instrucciones claras paso a paso.

Uso:
    python deploy_simple.py
"""

import os
import sys
import secrets
import webbrowser
import platform
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
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 70}{Colors.ENDC}\n")


def print_step(num, total, text):
    print(f"\n{Colors.CYAN}{Colors.BOLD}[Paso {num}/{total}] {text}{Colors.ENDC}")
    print("-" * 70)


def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_warning(text):
    print(f"{Colors.WARNING}⚠  {text}{Colors.ENDC}")


def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text):
    print(f"{Colors.CYAN}ℹ  {text}{Colors.ENDC}")


def wait_for_user(message="Presiona ENTER para continuar..."):
    input(f"\n{Colors.WARNING}{message}{Colors.ENDC}")


def check_python_version():
    """Verifica la versión de Python"""
    version = sys.version_info
    print(f"Python detectado: {version.major}.{version.minor}.{version.micro}")

    if version.major >= 3 and version.minor >= 9:
        print_success(f"Versión de Python compatible ✓")
        return True
    else:
        print_error(f"Se requiere Python 3.9 o superior")
        return False


def check_files():
    """Verifica que los archivos necesarios existan"""
    required_files = [
        'cloud_server/app.py',
        'cloud_server/requirements.txt',
        'bluetooth_gateway.py',
        'bluetooth_handler.py'
    ]

    missing = []
    for file in required_files:
        if not Path(file).exists():
            missing.append(file)

    if missing:
        print_error("Faltan archivos necesarios:")
        for f in missing:
            print(f"  - {f}")
        return False

    print_success("Todos los archivos necesarios presentes ✓")
    return True


def generate_secrets():
    """Genera claves secretas seguras"""
    return {
        'SECRET_KEY': secrets.token_urlsafe(32),
        'GATEWAY_SECRET_KEY': secrets.token_urlsafe(32)
    }


def step1_intro():
    """Introducción y verificación"""
    print_header("FILSYNC - DEPLOYMENT SIMPLIFICADO")

    print(f"{Colors.CYAN}Este script te guiará paso a paso para deployar tu aplicación.{Colors.ENDC}")
    print(f"{Colors.CYAN}NO requiere Git ni herramientas complejas.{Colors.ENDC}\n")

    print(f"{Colors.BOLD}Lo que necesitas:{Colors.ENDC}")
    print("  ✓ Python 3.9+ (YA LO TIENES)")
    print("  ✓ Cuenta GitHub (gratis)")
    print("  ✓ Cuenta Render (gratis)")
    print("  ✓ 10-15 minutos de tu tiempo\n")

    return True


def step2_verify():
    """Verifica requisitos"""
    print_step(1, 6, "Verificando Requisitos")

    if not check_python_version():
        return False

    if not check_files():
        print_error("Asegúrate de ejecutar este script desde la carpeta correcta")
        return False

    print_success("¡Todo listo para comenzar!")
    return True


def step3_github():
    """Instrucciones para GitHub"""
    print_step(2, 6, "Subir Código a GitHub")

    print(f"\n{Colors.BOLD}Vamos a subir tu código a GitHub (sin usar Git en la terminal){Colors.ENDC}\n")

    print("📋 OPCIÓN 1 - Subir archivos directamente (MÁS FÁCIL)")
    print("─" * 70)
    print("1. Ve a: " + Colors.CYAN + "https://github.com/new" + Colors.ENDC)
    print("2. Nombre del repositorio: " + Colors.BOLD + "filsync-cloud" + Colors.ENDC)
    print("3. Selecciona 'Public'")
    print("4. NO marques ninguna opción adicional")
    print("5. Haz clic en 'Create repository'")
    print("\n6. En la página que aparece, haz clic en:")
    print("   " + Colors.BOLD + "'uploading an existing file'" + Colors.ENDC)
    print("\n7. Arrastra TODA la carpeta 'cloud_server' a la ventana")
    print("8. Espera que suban todos los archivos")
    print("9. En 'Commit changes', escribe: 'Initial commit'")
    print("10. Haz clic en 'Commit changes'\n")

    print("─" * 70)
    print("\n📋 OPCIÓN 2 - Usar GitHub Desktop (si lo tienes)")
    print("─" * 70)
    print("1. Abre GitHub Desktop")
    print("2. File → Add Local Repository")
    print("3. Selecciona la carpeta 'cloud_server'")
    print("4. Publish repository\n")

    wait_for_user("Presiona ENTER cuando hayas subido el código a GitHub...")

    repo_url = input(
        f"\n{Colors.BOLD}Pega la URL de tu repositorio (ej: https://github.com/tu-usuario/filsync-cloud): {Colors.ENDC}").strip()

    if not repo_url:
        print_warning("URL no proporcionada, pero podemos continuar")
        repo_url = "https://github.com/tu-usuario/filsync-cloud"

    print_success("Código en GitHub ✓")
    return repo_url


def step4_render(secrets_dict):
    """Instrucciones para Render"""
    print_step(3, 6, "Deployment en Render")

    print(f"\n{Colors.BOLD}Ahora vamos a deployar en Render (hosting GRATIS){Colors.ENDC}\n")

    print("1️⃣  Crea tu cuenta en Render:")
    print("   " + Colors.CYAN + "https://render.com" + Colors.ENDC)
    print("   Haz clic en 'Get Started' y usa tu cuenta GitHub\n")

    wait_for_user("Presiona ENTER cuando hayas iniciado sesión en Render...")

    print("\n2️⃣  Crear el servicio web:")
    print("   a) En el dashboard, haz clic en 'New +' → 'Web Service'")
    print("   b) Click en 'Connect a repository' → Autoriza GitHub")
    print("   c) Busca y selecciona tu repositorio 'filsync-cloud'")
    print("   d) Haz clic en 'Connect'\n")

    wait_for_user("Presiona ENTER cuando hayas conectado el repositorio...")

    print("\n3️⃣  Configurar el servicio:")
    print("   " + Colors.BOLD + "Name:" + Colors.ENDC + " filsync-cloud")
    print("   " + Colors.BOLD + "Region:" + Colors.ENDC + " Oregon (o el más cercano)")
    print("   " + Colors.BOLD + "Branch:" + Colors.ENDC + " main")
    print("   " + Colors.BOLD + "Root Directory:" + Colors.ENDC + " (dejar vacío)")
    print("   " + Colors.BOLD + "Runtime:" + Colors.ENDC + " Python 3")
    print("   " + Colors.BOLD + "Build Command:" + Colors.ENDC + " pip install -r requirements.txt")
    print(
        "   " + Colors.BOLD + "Start Command:" + Colors.ENDC + " gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app")
    print("   " + Colors.BOLD + "Plan:" + Colors.ENDC + " Free\n")

    wait_for_user("Presiona ENTER cuando hayas configurado todo...")

    print("\n4️⃣  " + Colors.BOLD + "MUY IMPORTANTE - Variables de Entorno:" + Colors.ENDC)
    print("\n   Antes de crear el servicio, ve a 'Environment' y agrega:\n")
    print("   " + "─" * 70)
    print(f"   {Colors.BOLD}SECRET_KEY{Colors.ENDC}")
    print(f"   {secrets_dict['SECRET_KEY']}")
    print()
    print(f"   {Colors.BOLD}GATEWAY_SECRET_KEY{Colors.ENDC}")
    print(f"   {secrets_dict['GATEWAY_SECRET_KEY']}")
    print()
    print(f"   {Colors.BOLD}PORT{Colors.ENDC}")
    print(f"   8000")
    print()
    print(f"   {Colors.BOLD}OPENROUTER_API_KEY{Colors.ENDC} (opcional)")
    print(f"   tu-api-key-aqui")
    print("   " + "─" * 70)

    print(f"\n   {Colors.WARNING}¡GUARDA GATEWAY_SECRET_KEY EN UN LUGAR SEGURO!{Colors.ENDC}")
    print(f"   {Colors.WARNING}La necesitarás para configurar el gateway local{Colors.ENDC}\n")

    # Guardar secretos en archivo
    with open('secrets.txt', 'w') as f:
        f.write("SECRETOS GENERADOS - ¡GUARDA ESTE ARCHIVO!\n")
        f.write("=" * 70 + "\n\n")
        f.write(f"SECRET_KEY={secrets_dict['SECRET_KEY']}\n")
        f.write(f"GATEWAY_SECRET_KEY={secrets_dict['GATEWAY_SECRET_KEY']}\n\n")
        f.write("Usa GATEWAY_SECRET_KEY para configurar el gateway local\n")

    print_success(f"Secretos guardados en: {Colors.BOLD}secrets.txt{Colors.ENDC}")

    wait_for_user("Presiona ENTER cuando hayas configurado las variables de entorno...")

    print("\n5️⃣  Haz clic en 'Create Web Service'")
    print("   Render comenzará a deployar (toma 2-4 minutos)\n")

    wait_for_user("Presiona ENTER cuando el deployment esté COMPLETO (estado: Live)...")

    render_url = input(f"\n{Colors.BOLD}Copia y pega tu URL de Render aquí: {Colors.ENDC}").strip()

    if not render_url:
        print_warning("URL no proporcionada")
        render_url = "https://filsync-cloud-xxxx.onrender.com"

    if not render_url.startswith('http'):
        render_url = 'https://' + render_url

    print_success(f"Servidor deployado en: {render_url}")
    return render_url


def step5_configure_gateway(cloud_url, gateway_secret):
    """Configura el gateway local"""
    print_step(4, 6, "Configurar Gateway Local")

    print(f"\n{Colors.BOLD}Ahora configuraremos tu PC para conectarse al ESP32{Colors.ENDC}\n")

    # Detectar sistema operativo
    system = platform.system()

    print(f"Sistema detectado: {system}\n")

    # Tipo de Bluetooth
    print("1️⃣  Tipo de conexión Bluetooth:")
    print("   SPP = Bluetooth Classic (más común)")
    print("   BLE = Bluetooth Low Energy")
    bt_type = input(f"\n   Tipo (SPP/BLE) [SPP]: {Colors.ENDC}").strip().upper() or "SPP"

    # Puerto Bluetooth
    print(f"\n2️⃣  Puerto Bluetooth:")

    if system == "Windows":
        print("\n   En Windows:")
        print("   a) Ve a Configuración → Bluetooth y dispositivos")
        print("   b) Busca tu ESP32 en la lista")
        print("   c) Si no está pareado, páralo ahora")
        print("   d) Abre 'Administrador de dispositivos'")
        print("   e) Expande 'Puertos (COM y LPT)'")
        print("   f) Busca 'Standard Serial over Bluetooth' o similar")
        print("   g) Anota el número COM (ej: COM5)")
        default_port = "COM5"
    elif system == "Linux":
        print("\n   En Linux:")
        print("   a) Ejecuta: bluetoothctl")
        print("   b) scan on")
        print("   c) pair XX:XX:XX:XX:XX:XX (dirección de tu ESP32)")
        print("   d) Usa: /dev/rfcomm0")
        default_port = "/dev/rfcomm0"
    else:  # macOS
        print("\n   En macOS:")
        print("   a) Preferencias del Sistema → Bluetooth")
        print("   b) Paréa el ESP32")
        print("   c) Usa: /dev/cu.ESP32-SerialPort")
        default_port = "/dev/cu.ESP32-SerialPort"

    bt_port = input(f"\n   Puerto Bluetooth [{default_port}]: ").strip() or default_port

    # Crear archivo .env
    env_content = f"""# Configuración del Gateway Bluetooth Local
# Generado por deploy_simple.py

# URL del servidor cloud
CLOUD_SERVER_URL={cloud_url}

# Clave secreta compartida
GATEWAY_SECRET_KEY={gateway_secret}

# ID único de este gateway
GATEWAY_ID=gateway-001

# Configuración Bluetooth
BLUETOOTH_TYPE={bt_type}
BLUETOOTH_PORT={bt_port}
"""

    if bt_type == "BLE":
        env_content += """
# Configuración BLE (descomenta y completa)
# BLE_DEVICE_NAME=Filsync-ESP32
# BLE_SERVICE_UUID=tu-service-uuid
# BLE_CHAR_UUID=tu-characteristic-uuid
"""

    with open('.env', 'w') as f:
        f.write(env_content)

    print_success("Archivo .env creado ✓")

    # Resumen
    print(f"\n{Colors.BOLD}Configuración guardada:{Colors.ENDC}")
    print(f"  📡 Servidor Cloud: {cloud_url}")
    print(f"  🔵 Bluetooth: {bt_type} en {bt_port}")
    print(f"  📁 Archivo: .env\n")

    return True


def step6_test(cloud_url):
    """Verificar que todo funcione"""
    print_step(5, 6, "Verificar Instalación")

    print(f"\n{Colors.BOLD}Vamos a verificar que todo esté funcionando{Colors.ENDC}\n")

    print("1️⃣  Verificar servidor cloud:")
    print(f"   Abre: {Colors.CYAN}{cloud_url}/health{Colors.ENDC}")
    print("   Deberías ver algo como: {\"status\": \"healthy\", ...}\n")

    works = input(f"   ¿Funciona? (s/N): ").strip().lower()

    if works == 's':
        print_success("Servidor cloud funcionando ✓")
    else:
        print_warning("Si no funciona, espera 1-2 minutos (Render está iniciando)")
        print_warning("Luego recarga la página")

    return True


def step7_final():
    """Instrucciones finales"""
    print_step(6, 6, "¡Listo para Usar!")

    print_header("🎉 DEPLOYMENT COMPLETO")

    print(f"{Colors.GREEN}{Colors.BOLD}Tu aplicación está LISTA:{Colors.ENDC}\n")

    print("✅ Servidor cloud deployado en Render")
    print("✅ Código en GitHub")
    print("✅ Gateway local configurado")
    print("✅ Variables de entorno guardadas\n")

    print(f"{Colors.CYAN}{Colors.BOLD}PARA USAR LA APLICACIÓN:{Colors.ENDC}\n")

    print("1️⃣  Conecta tu ESP32 (debe estar encendido y con Bluetooth activo)")
    print()
    print("2️⃣  Ejecuta el gateway:")
    print(f"   {Colors.BOLD}python bluetooth_gateway.py{Colors.ENDC}")
    print()
    print("3️⃣  Abre tu navegador en la URL de Render")
    print("   (la URL está en el archivo .env)")
    print()
    print("4️⃣  ¡Disfruta de tu app en la nube!")
    print()

    print(f"{Colors.WARNING}NOTAS IMPORTANTES:{Colors.ENDC}")
    print("• El gateway debe estar corriendo para recibir datos del ESP32")
    print("• Tu PC debe estar encendida (solo para el Bluetooth)")
    print("• La primera carga puede tardar ~30 segundos")
    print("• El plan gratuito de Render duerme después de 15min sin uso\n")

    print(f"{Colors.CYAN}📚 Documentación:{Colors.ENDC}")
    print("• README.md - Guía completa")
    print("• LEEME_PRIMERO.md - Resumen ejecutivo")
    print("• ARQUITECTURA.md - Diagramas del sistema")
    print("• secrets.txt - Tus claves secretas (¡NO BORRAR!)\n")

    # Preguntar si quiere ejecutar el gateway ahora
    run_now = input(f"{Colors.BOLD}¿Ejecutar el gateway ahora? (s/N): {Colors.ENDC}").strip().lower()

    if run_now == 's':
        print(f"\n{Colors.CYAN}Ejecutando gateway...{Colors.ENDC}\n")
        print("=" * 70)
        os.system('python bluetooth_gateway.py')
    else:
        print(f"\n{Colors.INFO}Puedes ejecutarlo cuando quieras con:{Colors.ENDC}")
        print(f"{Colors.BOLD}python bluetooth_gateway.py{Colors.ENDC}\n")


def main():
    """Función principal"""
    try:
        # Paso 0: Intro
        if not step1_intro():
            return

        ready = input(f"{Colors.BOLD}¿Comenzamos? (s/N): {Colors.ENDC}").strip().lower()
        if ready != 's':
            print_info("Deployment cancelado. Ejecuta este script cuando estés listo.")
            return

        # Paso 1: Verificar
        if not step2_verify():
            return

        # Paso 2: GitHub
        repo_url = step3_github()

        # Generar secretos
        secrets_dict = generate_secrets()

        # Paso 3: Render
        cloud_url = step4_render(secrets_dict)

        # Paso 4: Configurar gateway
        if not step5_configure_gateway(cloud_url, secrets_dict['GATEWAY_SECRET_KEY']):
            return

        # Paso 5: Verificar
        if not step6_test(cloud_url):
            return

        # Paso 6: Final
        step7_final()

    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Deployment cancelado por el usuario{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.FAIL}Error: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()