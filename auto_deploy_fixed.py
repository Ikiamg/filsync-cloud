#!/usr/bin/env python3
"""
Script de Deployment Automático para Filsync Cloud
===================================================
Este script automatiza TODO el proceso de deployment:
1. Configura el proyecto localmente
2. Crea repositorio en GitHub
3. Hace deployment en Render
4. Configura el gateway local
5. ¡Todo listo para usar!

Requisitos:
- Python 3.9+
- Git instalado
- Cuenta GitHub
- Cuenta Render (se crea durante el proceso)

Uso:
    python auto_deploy.py
"""

import os
import sys
import json
import subprocess
import secrets
import webbrowser
import time
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


def print_step(num, text):
    print(f"\n{Colors.CYAN}{Colors.BOLD}[{num}/8] {text}{Colors.ENDC}")
    print("-" * 70)


def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")


def print_warning(text):
    print(f"{Colors.WARNING}⚠  {text}{Colors.ENDC}")


def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_info(text):
    print(f"{Colors.CYAN}ℹ  {text}{Colors.ENDC}")


def run_command(cmd, cwd=None, capture=False):
    """Ejecuta un comando y retorna el resultado"""
    try:
        if capture:
            result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, cwd=cwd, check=True)
            return True
    except subprocess.CalledProcessError as e:
        return False


def find_project_root():
    """Encuentra la raíz del proyecto"""
    current = Path.cwd()

    # Buscar cloud_server en el directorio actual y padres
    for parent in [current] + list(current.parents):
        cloud_server_path = parent / 'cloud_server'
        if cloud_server_path.exists() and cloud_server_path.is_dir():
            print_success(f"Proyecto encontrado en: {parent}")
            return parent

    # Si no encontramos cloud_server, buscar si estamos DENTRO de cloud_server
    if current.name == 'cloud_server':
        print_success(f"Estamos dentro de cloud_server: {current}")
        return current

    # No encontrado
    print_error("No se encontró la carpeta 'cloud_server'")
    print_info("Asegúrate de ejecutar este script desde la carpeta del proyecto Filsync")
    return None


def check_git():
    """Verifica que Git esté instalado"""
    if run_command(['git', '--version'], capture=True):
        print_success("Git instalado")
        return True
    else:
        print_error("Git no encontrado. Instálalo desde: https://git-scm.com/")
        return False


def check_github_cli():
    """Verifica si GitHub CLI está instalado"""
    if run_command(['gh', '--version'], capture=True):
        print_success("GitHub CLI instalado")
        return True
    else:
        print_warning("GitHub CLI no encontrado (usaremos método manual)")
        return False


def install_dependencies():
    """Instala las dependencias necesarias"""
    print_info("Instalando dependencias de Python...")

    packages = [
        'requests',
        'python-dotenv',
    ]

    for pkg in packages:
        print(f"  Instalando {pkg}...", end=' ')
        sys.stdout.flush()
        if run_command([sys.executable, '-m', 'pip', 'install', '-q', pkg]):
            print_success("✓")
        else:
            print_error("✗")
            return False

    return True


def create_github_repo(cloud_server_path):
    """Crea repositorio en GitHub"""
    print_info("Vamos a crear un repositorio en GitHub...")

    # Verificar si ya existe un repo
    git_path = cloud_server_path / '.git'
    if git_path.exists():
        print_warning("Ya existe un repositorio Git en cloud_server")

        overwrite = input(f"{Colors.WARNING}¿Reinicializar? (s/N): {Colors.ENDC}").strip().lower()
        if overwrite != 's':
            print_info("Usando repositorio existente")
            return True
        else:
            # Eliminar .git anterior
            import shutil
            shutil.rmtree(git_path)

    repo_name = input(f"\n{Colors.BOLD}Nombre del repositorio (default: filsync-cloud): {Colors.ENDC}").strip()
    if not repo_name:
        repo_name = "filsync-cloud"

    # Inicializar Git
    print_info("Inicializando repositorio Git...")
    if not run_command(['git', 'init'], cwd=str(cloud_server_path)):
        print_error("Error inicializando Git")
        return False

    # Configurar Git
    run_command(['git', 'config', 'user.name', 'Filsync'], cwd=str(cloud_server_path))
    run_command(['git', 'config', 'user.email', 'filsync@example.com'], cwd=str(cloud_server_path))

    # Crear .gitignore si no existe
    gitignore_path = cloud_server_path / '.gitignore'
    if not gitignore_path.exists():
        with open(gitignore_path, 'w') as f:
            f.write("__pycache__/\n*.pyc\n.env\n*.log\nvenv/\n")

    # Hacer commit inicial
    run_command(['git', 'add', '.'], cwd=str(cloud_server_path))
    run_command(['git', 'commit', '-m', 'Initial commit - Filsync Cloud Server'], cwd=str(cloud_server_path))
    run_command(['git', 'branch', '-M', 'main'], cwd=str(cloud_server_path))

    print_success("Repositorio Git creado localmente")

    # Preguntar si quiere usar GitHub CLI o manual
    print(f"\n{Colors.BOLD}¿Cómo quieres subir el código a GitHub?{Colors.ENDC}")
    print("1. GitHub CLI (automático - si tienes 'gh' instalado)")
    print("2. Manual (te daré instrucciones paso a paso)")

    choice = input(f"\n{Colors.BOLD}Opción (1/2): {Colors.ENDC}").strip()

    if choice == '1' and check_github_cli():
        # Usar GitHub CLI
        print_info("Creando repositorio con GitHub CLI...")

        # Autenticar si es necesario
        if not run_command(['gh', 'auth', 'status'], capture=True):
            print_info("Iniciando autenticación con GitHub...")
            run_command(['gh', 'auth', 'login'], cwd=str(cloud_server_path))

        # Crear repo
        if run_command(['gh', 'repo', 'create', repo_name, '--public', '--source=.', '--push'],
                       cwd=str(cloud_server_path)):
            print_success(f"Repositorio creado y código subido")
            return True
        else:
            print_error("Error creando repositorio con GitHub CLI")
            print_info("Intentemos el método manual...")
            # Continuar con método manual

    # Método manual
    print_info("\n" + "=" * 70)
    print_info("INSTRUCCIONES PARA SUBIR A GITHUB MANUALMENTE:")
    print_info("=" * 70)
    print(f"\n1. Abre tu navegador en: {Colors.CYAN}https://github.com/new{Colors.ENDC}")
    print(f"2. Nombre del repositorio: {Colors.BOLD}{repo_name}{Colors.ENDC}")
    print("3. Selecciona 'Public' (o Private si prefieres)")
    print("4. NO marques 'Initialize with README'")
    print("5. Haz clic en 'Create repository'")

    input(f"\n{Colors.WARNING}Presiona ENTER cuando hayas creado el repositorio en GitHub...{Colors.ENDC}")

    print("\n6. GitHub te mostrará instrucciones. Copia la URL del repositorio")
    print("   Ejemplo: https://github.com/tu-usuario/filsync-cloud.git")

    repo_url = input(f"\n{Colors.BOLD}Pega la URL de tu repositorio aquí: {Colors.ENDC}").strip()

    if not repo_url:
        print_error("URL requerida")
        return False

    # Push al repo
    print_info("Subiendo código a GitHub...")
    if not run_command(['git', 'remote', 'add', 'origin', repo_url], cwd=str(cloud_server_path)):
        # Si falla, posiblemente ya existe
        run_command(['git', 'remote', 'remove', 'origin'], cwd=str(cloud_server_path))
        run_command(['git', 'remote', 'add', 'origin', repo_url], cwd=str(cloud_server_path))

    if run_command(['git', 'push', '-u', 'origin', 'main'], cwd=str(cloud_server_path)):
        print_success("Código subido a GitHub exitosamente")
        return True
    else:
        print_error("Error subiendo a GitHub")
        print_info("Verifica que la URL sea correcta y tengas permisos")
        return False


def generate_secrets():
    """Genera claves secretas seguras"""
    return {
        'SECRET_KEY': secrets.token_urlsafe(32),
        'GATEWAY_SECRET_KEY': secrets.token_urlsafe(32)
    }


def setup_render():
    """Guía para configurar Render"""
    print_info("\n" + "=" * 70)
    print_info("CONFIGURACIÓN DE RENDER")
    print_info("=" * 70)

    print(f"\n{Colors.BOLD}Ahora vamos a deployar en Render (plataforma cloud GRATIS){Colors.ENDC}\n")

    print("Voy a abrir Render en tu navegador...")
    time.sleep(1)
    webbrowser.open("https://render.com")

    print("\n1️⃣  En Render:")
    print("     - Si no tienes cuenta: Haz clic en 'Get Started'")
    print("     - Inicia sesión con GitHub (MUY recomendado)")

    input(f"\n{Colors.WARNING}Presiona ENTER cuando hayas iniciado sesión en Render...{Colors.ENDC}")

    print("\n2️⃣  En el dashboard de Render:")
    print("     - Haz clic en 'New +' (arriba a la derecha)")
    print("     - Selecciona 'Web Service'")
    print("     - Conecta tu repositorio GitHub (el que acabas de crear)")
    print(f"     - Render detectará que es Python automáticamente")

    input(f"\n{Colors.WARNING}Presiona ENTER cuando hayas conectado el repositorio...{Colors.ENDC}")

    print("\n3️⃣  Configuración del servicio:")
    print("     Name: puedes dejarlo como está o cambiar el nombre")
    print("     Branch: main")
    print("     Build Command: pip install -r requirements.txt")
    print("     Start Command: gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app")

    input(f"\n{Colors.WARNING}Presiona ENTER para continuar...{Colors.ENDC}")

    # Generar secretos
    secrets_dict = generate_secrets()

    print(f"\n4️⃣  {Colors.BOLD}MUY IMPORTANTE - Variables de Entorno:{Colors.ENDC}")
    print("\n     En la sección 'Environment', agrega estas variables:")
    print("\n" + "=" * 70)
    print(f"{Colors.CYAN}SECRET_KEY{Colors.ENDC}={secrets_dict['SECRET_KEY']}")
    print(f"{Colors.CYAN}GATEWAY_SECRET_KEY{Colors.ENDC}={secrets_dict['GATEWAY_SECRET_KEY']}")
    print(f"{Colors.CYAN}OPENROUTER_API_KEY{Colors.ENDC}=tu-api-key-aqui (opcional para IA)")
    print("=" * 70)

    print(f"\n{Colors.WARNING}⚠️  ¡COPIA Y GUARDA GATEWAY_SECRET_KEY!{Colors.ENDC}")
    print(f"{Colors.WARNING}    La necesitarás en el siguiente paso{Colors.ENDC}")

    # Guardar en archivo temporal para no perderlo
    with open('SECRETS_TEMP.txt', 'w') as f:
        f.write(f"SECRET_KEY={secrets_dict['SECRET_KEY']}\n")
        f.write(f"GATEWAY_SECRET_KEY={secrets_dict['GATEWAY_SECRET_KEY']}\n")

    print_info(f"\n💾 Secretos guardados en: SECRETS_TEMP.txt")

    input(f"\n{Colors.WARNING}Presiona ENTER cuando hayas configurado las variables...{Colors.ENDC}")

    print("\n5️⃣  Plan y Deploy:")
    print("     - Selecciona el plan 'Free'")
    print("     - Haz clic en 'Create Web Service'")
    print("     - Render comenzará a deployar (toma 2-3 minutos)")

    print(f"\n{Colors.INFO}Puedes ver el progreso en los logs de Render...{Colors.ENDC}")

    input(f"\n{Colors.WARNING}Presiona ENTER cuando veas 'Live' (deployment completo)...{Colors.ENDC}")

    print("\n6️⃣  Copia la URL de tu aplicación:")
    print("     Está arriba en Render, algo como:")
    print("     https://filsync-cloud-xxxx.onrender.com")

    render_url = input(f"\n{Colors.BOLD}Pega tu URL aquí: {Colors.ENDC}").strip()

    if not render_url:
        print_error("URL requerida")
        return None, None

    # Asegurar que tenga https://
    if not render_url.startswith('http'):
        render_url = f"https://{render_url}"

    print_success(f"Servidor cloud deployado en: {render_url}")

    return render_url, secrets_dict['GATEWAY_SECRET_KEY']


def configure_local_gateway(project_root, cloud_url, gateway_secret):
    """Configura el gateway local"""
    print_info("Configurando gateway local...")

    # Preguntar configuración de Bluetooth
    print(f"\n{Colors.BOLD}Configuración de Bluetooth:{Colors.ENDC}")

    import platform
    system = platform.system()

    bt_type = input("Tipo de Bluetooth (SPP/BLE) [SPP]: ").strip().upper() or "SPP"

    if bt_type == "SPP":
        if system == "Windows":
            default_port = "COM5"
            print(f"En Windows, busca tu puerto COM en:")
            print(f"Settings → Bluetooth & devices → Devices → More options")
        else:
            default_port = "/dev/rfcomm0"

        bt_port = input(f"Puerto Bluetooth [{default_port}]: ").strip() or default_port
        ble_config = ""
    else:
        bt_port = ""
        ble_device = input("Nombre del dispositivo BLE [Filsync-ESP32]: ").strip() or "Filsync-ESP32"
        ble_config = f"\nBLE_DEVICE_NAME={ble_device}\n# BLE_SERVICE_UUID=tu-service-uuid\n# BLE_CHAR_UUID=tu-characteristic-uuid"

    # Crear archivo .env en la raíz del proyecto
    env_path = project_root / '.env'

    env_content = f"""# Configuración del Gateway Bluetooth Local
# Generado automáticamente por auto_deploy.py

# URL del servidor cloud
CLOUD_SERVER_URL={cloud_url}

# Clave secreta (debe ser la misma que en el servidor cloud)
GATEWAY_SECRET_KEY={gateway_secret}

# ID único de este gateway
GATEWAY_ID=gateway-001

# Configuración Bluetooth
BLUETOOTH_TYPE={bt_type}
"""

    if bt_type == "SPP":
        env_content += f"BLUETOOTH_PORT={bt_port}\n"
    else:
        env_content += ble_config + "\n"

    with open(env_path, 'w') as f:
        f.write(env_content)

    print_success(f"Archivo .env creado en: {env_path}")

    # Mostrar resumen
    print(f"\n{Colors.BOLD}Configuración del Gateway:{Colors.ENDC}")
    print(f"  Servidor Cloud: {cloud_url}")
    print(f"  Bluetooth: {bt_type}" + (f" en {bt_port}" if bt_port else ""))

    return True


def test_deployment(cloud_url):
    """Verifica que el deployment funcione"""
    try:
        import requests
    except ImportError:
        print_warning("requests no instalado, saltando verificación")
        return True

    print_info(f"Verificando deployment en {cloud_url}...")

    try:
        response = requests.get(f"{cloud_url}/health", timeout=15)
        if response.status_code == 200:
            print_success("¡Servidor cloud respondiendo correctamente!")
            data = response.json()
            print_info(f"Status: {data.get('status', 'unknown')}")
            return True
        else:
            print_warning(f"Servidor respondió con código: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print_warning("Timeout - Render puede estar iniciando (espera ~30 segundos)")
        return False
    except Exception as e:
        print_warning(f"No se pudo verificar: {e}")
        print_info("Esto es normal si Render aún está iniciando")
        return False


def show_final_instructions(project_root, cloud_url):
    """Muestra las instrucciones finales"""
    print_header("🎉 ¡DEPLOYMENT COMPLETO!")

    print(f"{Colors.GREEN}{Colors.BOLD}Tu aplicación está LISTA para usar:{Colors.ENDC}\n")

    print(f"✅ Servidor cloud: {cloud_url}")
    print(f"✅ Repositorio en GitHub creado")
    print(f"✅ Gateway local configurado")
    print(f"✅ Archivo .env creado\n")

    print(f"{Colors.CYAN}{Colors.BOLD}CÓMO USAR TU APLICACIÓN:{Colors.ENDC}\n")

    print("1️⃣  Ejecutar el Gateway Local (en esta carpeta):")
    print(f"   {Colors.BOLD}python bluetooth_gateway.py{Colors.ENDC}\n")

    print("2️⃣  Abrir la aplicación web:")
    print(f"   {Colors.CYAN}{cloud_url}{Colors.ENDC}\n")

    print("3️⃣  Conectar el ESP32:")
    print("   El gateway detectará automáticamente la conexión Bluetooth\n")

    print(f"{Colors.WARNING}⚠️  IMPORTANTE:{Colors.ENDC}")
    print(f"   - La primera carga puede tardar ~30 segundos")
    print(f"   - Mantén el gateway ejecutándose mientras uses la app")
    print(f"   - Tu PC debe estar encendida para recibir datos del ESP32\n")

    print(f"{Colors.CYAN}📚 Documentación:{Colors.ENDC}")
    print(f"   - LEEME_PRIMERO.md - Resumen completo")
    print(f"   - README.md - Documentación detallada")
    print(f"   - ARQUITECTURA.md - Cómo funciona el sistema\n")


def main():
    """Función principal del deployment automático"""
    print_header("FILSYNC - DEPLOYMENT AUTOMÁTICO")

    print(f"{Colors.CYAN}Este script automatizará TODO el proceso de deployment.{Colors.ENDC}")
    print(f"{Colors.CYAN}Solo sigue las instrucciones en pantalla 🚀{Colors.ENDC}\n")

    print(f"{Colors.WARNING}Requisitos:{Colors.ENDC}")
    print("  ✓ Python 3.9+ (ya lo tienes)")
    print("  ✓ Git instalado")
    print("  ✓ Cuenta GitHub (gratis)")
    print("  ✓ Cuenta Render (gratis - la crearemos)\n")

    ready = input(f"{Colors.BOLD}¿Listo para comenzar? (s/N): {Colors.ENDC}").strip().lower()
    if ready != 's':
        print_info("Deployment cancelado. Ejecuta de nuevo cuando estés listo.")
        return

    # Paso 0: Encontrar el proyecto
    print_step(1, "Localizando Proyecto")
    project_root = find_project_root()
    if not project_root:
        print_error("\n❌ No se encontró cloud_server/")
        print_info("Asegúrate de estar en la carpeta correcta del proyecto")
        return

    cloud_server_path = project_root / 'cloud_server' if project_root.name != 'cloud_server' else project_root

    # Paso 1: Verificar requisitos
    print_step(2, "Verificando Requisitos")
    if not check_git():
        print_error("Deployment fallido: Git requerido")
        return

    # Paso 2: Instalar dependencias
    print_step(3, "Instalando Dependencias Python")
    if not install_dependencies():
        print_error("Deployment fallido: Error instalando dependencias")
        return

    # Paso 3: Crear repositorio GitHub
    print_step(4, "Creando Repositorio en GitHub")
    if not create_github_repo(cloud_server_path):
        print_error("Deployment fallido: Error con GitHub")
        return

    # Paso 4: Deployment en Render
    print_step(5, "Deployment en Render")
    cloud_url, gateway_secret = setup_render()

    if not cloud_url or not gateway_secret:
        print_error("Deployment fallido: Error configurando Render")
        return

    # Paso 5: Configurar gateway local
    print_step(6, "Configurando Gateway Local")
    if not configure_local_gateway(project_root, cloud_url, gateway_secret):
        print_error("Deployment fallido: Error configurando gateway")
        return

    # Paso 6: Verificar deployment
    print_step(7, "Verificando Deployment")
    test_deployment(cloud_url)

    # Paso 7: Instrucciones finales
    print_step(8, "¡Todo Listo!")
    show_final_instructions(project_root, cloud_url)

    # Limpiar archivo temporal de secretos
    temp_file = Path('SECRETS_TEMP.txt')
    if temp_file.exists():
        temp_file.unlink()

    print(f"\n{Colors.GREEN}{'=' * 70}{Colors.ENDC}")
    print(f"{Colors.GREEN}{Colors.BOLD}{'¡Gracias por usar Filsync Cloud!':^70}{Colors.ENDC}")
    print(f"{Colors.GREEN}{'=' * 70}{Colors.ENDC}\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.WARNING}Deployment cancelado por el usuario{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.FAIL}Error inesperado: {e}{Colors.ENDC}")
        import traceback

        traceback.print_exc()
        sys.exit(1)