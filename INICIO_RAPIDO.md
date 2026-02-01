# ⚡ Inicio Rápido - Filsync Cloud

¿Quieres tener tu aplicación corriendo en la nube en **menos de 10 minutos**? Sigue esta guía.

## 🎯 Lo que vas a lograr

Al final de esta guía tendrás:
- ✅ Servidor web corriendo en la nube (gratis)
- ✅ Gateway local conectándose a tu ESP32
- ✅ Datos fluyendo en tiempo real
- ✅ Acceso desde cualquier dispositivo

## 📋 Pre-requisitos

- [ ] Python 3.9+ instalado
- [ ] ESP32 con Bluetooth
- [ ] Cuenta GitHub (gratis)
- [ ] 10 minutos de tu tiempo ⏱️

## 🚀 Pasos Rápidos

### 1. Descargar el Proyecto (30 segundos)

Ya tienes los archivos, pero si necesitas clonarlos:

```bash
git clone https://github.com/TU_USUARIO/filsync-cloud.git
cd filsync-cloud
```

### 2. Setup Automático (2 minutos)

```bash
python setup.py
```

Este script te preguntará:
1. URL del servidor cloud (por ahora usa `http://localhost:8000`)
2. Clave secreta (se genera automáticamente)
3. Tipo de Bluetooth (SPP o BLE)
4. Puerto COM de tu ESP32

### 3. Deploy en Render (5 minutos)

#### 3.1 Subir a GitHub

```bash
cd cloud_server
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/filsync-cloud.git
git push -u origin main
```

#### 3.2 Crear servicio en Render

1. Ve a https://render.com
2. Login con GitHub
3. Click en "New +" → "Web Service"
4. Selecciona tu repo `filsync-cloud`
5. Configuración:
   - **Name**: `filsync-cloud`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --worker-class eventlet -w 1 --bind 0.0.0.0:$PORT app:app`

#### 3.3 Variables de Entorno

En Render, agrega estas variables:

```
SECRET_KEY=cualquier-string-aleatorio-aqui
GATEWAY_SECRET_KEY=la-clave-del-paso-2
OPENROUTER_API_KEY=tu-api-key (opcional)
```

**IMPORTANTE**: Copia el `GATEWAY_SECRET_KEY` que se generó en el paso 2.

Click en "Create Web Service" → Espera 2-3 minutos

### 4. Actualizar .env Local (30 segundos)

Edita tu archivo `.env` y cambia:

```env
CLOUD_SERVER_URL=https://tu-app.onrender.com  # ← URL que te dio Render
```

### 5. ¡Ejecutar! (10 segundos)

```bash
python bluetooth_gateway.py
```

Deberías ver:

```
✓ Conexión establecida con el cloud
✓ Bluetooth iniciado correctamente
🚀 GATEWAY EN EJECUCIÓN
```

### 6. Abrir en el Navegador

Ve a: `https://tu-app.onrender.com`

## 🎉 ¡Listo!

Si todo funcionó, deberías ver:
- ✅ Interfaz web cargando
- ✅ Datos del ESP32 apareciendo en tiempo real
- ✅ Gráficas actualizándose

## ❌ ¿Algo salió mal?

### Gateway no conecta al cloud

```bash
# Verificar que el servidor está arriba
curl https://tu-app.onrender.com/health
```

**Soluciones**:
- Espera 2-3 minutos (Render puede tardar en iniciar)
- Verifica que la URL tenga `https://`
- Confirma que `GATEWAY_SECRET_KEY` sea la misma en ambos lados

### ESP32 no conecta

**Windows**:
```
Settings → Bluetooth → Ver dispositivos pareados
```

**Linux**:
```bash
bluetoothctl
scan on
pair XX:XX:XX:XX:XX:XX
```

**Mac**:
```
System Preferences → Bluetooth → Devices
```

Asegúrate de que el puerto COM sea correcto en `.env`

### No veo datos en la web

1. Abre la consola del navegador (F12)
2. Busca errores de WebSocket
3. Verifica que el gateway esté conectado:
   ```bash
   # En la terminal del gateway debe decir:
   🟢 CONECTADO
   ```

## 📚 Próximos Pasos

Ahora que tienes lo básico funcionando:

1. **Personaliza la interfaz**: Edita `cloud_server/templates/index.html`
2. **Agrega alertas**: Configura umbrales en `cloud_server/app.py`
3. **Base de datos**: Sigue la guía de PostgreSQL
4. **Dominio propio**: Conecta tu dominio en Render

## 🆘 Necesitas Ayuda

- 📖 Documentación completa: `README.md`
- 🚀 Guías de deployment: `deployment_guides/`
- 💬 Abre un issue en GitHub

---

**Tiempo total**: ~10 minutos ⏱️

**Costo**: $0 💰

**Complejidad**: Baja 🟢