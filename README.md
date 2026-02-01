# 🏥 Filsync - Sistema de Monitoreo Biométrico Cloud

<div align="center">

![Filsync](https://img.shields.io/badge/Filsync-Cloud%20Ready-blue)
![Python](https://img.shields.io/badge/Python-3.9+-green)
![Flask](https://img.shields.io/badge/Flask-3.0-red)
![ESP32](https://img.shields.io/badge/ESP32-Bluetooth-orange)

**Sistema de monitoreo de signos vitales en tiempo real con ESP32, IA y arquitectura cloud híbrida**

[Características](#-características) • [Arquitectura](#-arquitectura) • [Instalación](#-instalación-rápida) • [Deployment](#-deployment) • [Documentación](#-documentación)

</div>

---

## 🎯 Características

- 📡 **Conexión Bluetooth** con ESP32 (SPP o BLE)
- 🌐 **Interfaz Web en Tiempo Real** con WebSockets
- 🤖 **Análisis con IA** usando OpenRouter
- ☁️ **Arquitectura Híbrida Cloud**: Gateway local + Servidor cloud
- 📊 **Gráficas en Tiempo Real** de FC, SpO2 y Temperatura
- 🚨 **Sistema de Alertas** automático
- 📱 **Responsive Design** - funciona en móvil y desktop
- 🔒 **Seguro** con autenticación entre gateway y servidor

## 📐 Arquitectura

```
┌─────────────────────┐
│   ESP32 Bluetooth   │  ← Sensor biométrico (MAX30102)
└──────────┬──────────┘
           │ Bluetooth
           ▼
┌─────────────────────┐
│  Gateway Local      │  ← Corre en tu PC
│  (bluetooth_gateway)│     - Se conecta al ESP32
└──────────┬──────────┘     - Envía datos al cloud
           │ HTTPS
           ▼
┌─────────────────────┐
│  Cloud Server       │  ← Corre en Render/Railway
│  (cloud_server)     │     - Interfaz web
└──────────┬──────────┘     - Procesamiento IA
           │                - Base de datos
           ▼
┌─────────────────────┐
│  Usuarios Web       │  ← Acceso desde cualquier
│  (Navegador)        │     dispositivo
└─────────────────────┘
```

### ¿Por qué arquitectura híbrida?

**Problema**: Bluetooth requiere acceso físico al hardware, pero queremos un servidor rápido en la nube.

**Solución**: 
- ✅ Gateway local (ligero) maneja solo Bluetooth
- ✅ Servidor cloud maneja todo lo pesado (web, IA, base de datos)
- ✅ Usuarios acceden al cloud (rápido, disponible 24/7)
- ✅ El ESP32 sigue conectándose localmente

## 🚀 Instalación Rápida

### Requisitos Previos

- Python 3.9 o superior
- ESP32 con Bluetooth
- Cuenta en [Render](https://render.com) o [Railway](https://railway.app) (gratis)
- API Key de [OpenRouter](https://openrouter.ai) (opcional, para IA)

### 1. Clonar el Repositorio

```bash
git clone https://github.com/TU_USUARIO/filsync-cloud.git
cd filsync-cloud
```

### 2. Deploy del Servidor Cloud

Elige una plataforma:

#### Opción A: Render (Recomendada)
Ver guía completa: [`deployment_guides/RENDER_DEPLOYMENT.md`](deployment_guides/RENDER_DEPLOYMENT.md)

#### Opción B: Railway
Ver guía completa: [`deployment_guides/RAILWAY_DEPLOYMENT.md`](deployment_guides/RAILWAY_DEPLOYMENT.md)

### 3. Configurar Gateway Local

```bash
# Instalar dependencias
pip install -r requirements.txt

# Copiar archivo de configuración
cp .env.gateway.example .env

# Editar .env con tus valores
nano .env
```

Tu archivo `.env` debe contener:

```env
CLOUD_SERVER_URL=https://tu-app.onrender.com  # URL de tu servidor cloud
GATEWAY_SECRET_KEY=tu-clave-secreta           # La misma que en el cloud
BLUETOOTH_TYPE=SPP                             # o BLE
BLUETOOTH_PORT=COM5                            # Tu puerto Bluetooth
```

### 4. Ejecutar el Gateway

```bash
python bluetooth_gateway.py
```

Deberías ver:

```
🌐 Conectando al servidor cloud...
✓ Conexión establecida con el cloud
📱 Iniciando conexión Bluetooth...
✓ Bluetooth iniciado correctamente
🚀 GATEWAY EN EJECUCIÓN
```

### 5. Acceder a la Aplicación

Abre tu navegador en: `https://tu-app.onrender.com`

¡Listo! 🎉

## 📁 Estructura del Proyecto

```
filsync-cloud/
├── cloud_server/              # Servidor que corre en la nube
│   ├── app.py                # Aplicación Flask principal
│   ├── ai_service.py         # Servicio de IA
│   ├── requirements.txt      # Dependencias
│   ├── Procfile             # Para Heroku/Railway
│   ├── render.yaml          # Para Render
│   ├── templates/           # Templates HTML
│   └── static/              # CSS, JS, imágenes
│
├── bluetooth_gateway.py      # Gateway local (corre en tu PC)
├── bluetooth_handler.py      # Manejador de Bluetooth
├── .env.gateway.example     # Ejemplo de configuración local
│
├── deployment_guides/        # Guías de deployment
│   ├── RENDER_DEPLOYMENT.md
│   └── RAILWAY_DEPLOYMENT.md
│
└── README.md                # Este archivo
```

## 🔧 Configuración

### Variables de Entorno - Servidor Cloud

```env
SECRET_KEY=clave-aleatoria-para-flask
GATEWAY_SECRET_KEY=clave-compartida-con-gateway
OPENROUTER_API_KEY=tu-api-key-openrouter
PORT=8000
```

### Variables de Entorno - Gateway Local

```env
CLOUD_SERVER_URL=https://tu-app.onrender.com
GATEWAY_SECRET_KEY=misma-clave-que-cloud
GATEWAY_ID=gateway-001
BLUETOOTH_TYPE=SPP
BLUETOOTH_PORT=COM5
```

## 📊 Endpoints API

### Públicos (Web)

- `GET /` - Interfaz web principal
- `GET /api/status` - Estado actual del sistema
- `GET /api/alerts` - Alertas recientes
- `POST /api/ai_tips` - Generar consejos con IA
- `GET /health` - Health check

### Privados (Gateway)

Requieren header `X-Gateway-Secret`

- `POST /api/gateway/register` - Registrar gateway
- `GET /api/gateway/ping` - Ping periódico
- `POST /api/gateway/data` - Enviar datos biométricos

## 🧪 Desarrollo Local

Para probar todo localmente sin deployment:

```bash
# Terminal 1: Servidor Cloud Local
cd cloud_server
pip install -r requirements.txt
python app.py

# Terminal 2: Gateway
python bluetooth_gateway.py
```

Accede a: `http://localhost:8000`

## 🔒 Seguridad

- ✅ Autenticación entre gateway y servidor con clave compartida
- ✅ HTTPS automático en producción
- ✅ Validación de datos entrantes
- ✅ Sin credenciales hardcodeadas (todo por variables de entorno)

## 📈 Escalabilidad

### Almacenamiento Persistente

Por defecto, los datos se almacenan en memoria (se pierden al reiniciar).

Para producción, agrega PostgreSQL:

1. **Render**: Add-on PostgreSQL ($7/mes)
2. **Railway**: Agregar servicio PostgreSQL
3. Actualizar `app.py` para usar SQLAlchemy

### Múltiples Gateways

Puedes tener varios ESP32 enviando datos simultáneamente:

1. Cada gateway necesita un `GATEWAY_ID` único
2. El servidor automáticamente distingue entre ellos
3. Los datos se mezclan en tiempo real en la interfaz

## 🆘 Troubleshooting

### Gateway no se conecta al cloud

```bash
# Verificar conectividad
curl https://tu-app.onrender.com/health

# Revisar logs
python bluetooth_gateway.py
```

**Soluciones comunes**:
- Verifica que `CLOUD_SERVER_URL` tenga `https://`
- Confirma que `GATEWAY_SECRET_KEY` sea idéntica
- Revisa el firewall/antivirus

### ESP32 no conecta vía Bluetooth

**Windows**:
1. Settings → Bluetooth → Devices
2. Encuentra "ESP32" o tu nombre de dispositivo
3. Parear si no está pareado
4. Nota el puerto COM (ej: COM5)

**Linux**:
```bash
sudo rfcomm bind 0 XX:XX:XX:XX:XX:XX  # Dirección BT del ESP32
# Usar /dev/rfcomm0 como BLUETOOTH_PORT
```

**Mac**:
```bash
ls /dev/cu.*  # Buscar dispositivo Bluetooth
# Usar /dev/cu.ESP32-SerialPort como BLUETOOTH_PORT
```

### Errores de deployment

Ver logs en la plataforma:
- **Render**: Dashboard → Logs
- **Railway**: Deployments → View Logs

## 📚 Documentación Adicional

- [Guía de Deployment en Render](deployment_guides/RENDER_DEPLOYMENT.md)
- [Guía de Deployment en Railway](deployment_guides/RAILWAY_DEPLOYMENT.md)
- [Documentación de OpenRouter](https://openrouter.ai/docs)

## 🤝 Contribuir

Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea una rama: `git checkout -b feature/nueva-caracteristica`
3. Commit: `git commit -m 'Agregar nueva característica'`
4. Push: `git push origin feature/nueva-caracteristica`
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo licencia MIT. Ver `LICENSE` para más detalles.

## 🙏 Agradecimientos

- ESP32 community
- Flask & SocketIO
- OpenRouter para IA
- Render & Railway por hosting gratuito

---

<div align="center">

**¿Necesitas ayuda?** Abre un [Issue](https://github.com/TU_USUARIO/filsync-cloud/issues)

Hecho con ❤️ para monitoreo de salud

</div>