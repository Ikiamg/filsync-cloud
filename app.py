"""
Servidor Cloud para Filsync
============================
Este servidor corre en la nube (Render, Railway, etc.) y:
1. Recibe datos del gateway local vía HTTP
2. Sirve la interfaz web a los usuarios
3. Procesa análisis con IA
4. Almacena datos históricos

No requiere Bluetooth - los datos llegan desde el gateway local.
"""

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import logging
import sys
import os
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dotenv import load_dotenv

load_dotenv()

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Crear aplicación
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'cloud-secret-key-change-me')
CORS(app)

# Inicializar SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Importar servicios
try:
    from ai_service import AIService
    ai_service = AIService()
    logger.info("✓ Servicio de IA inicializado")
except Exception as e:
    logger.warning(f"⚠️  No se pudo inicializar IA: {e}")
    ai_service = None

# Almacenamiento en memoria (en producción usar Redis/PostgreSQL)
class DataStore:
    def __init__(self, max_points=200):
        self.current_data = {
            'fc': 0,
            'spo2': 0,
            'temp': 0.0,
            'state': 'SIN_DEDO',
            'timestamp': datetime.now().isoformat()
        }
        
        # Buffers para gráficas (últimos N puntos)
        self.max_points = max_points
        self.fc_buffer = deque(maxlen=max_points)
        self.spo2_buffer = deque(maxlen=max_points)
        self.temp_buffer = deque(maxlen=max_points)
        self.timestamps = deque(maxlen=max_points)
        
        # Gateways registrados
        self.gateways = {}
        self.gateway_last_seen = {}
        
        # Historial de alertas
        self.alerts = deque(maxlen=50)
        
    def update(self, data):
        """Actualiza los datos actuales"""
        self.current_data.update({
            'fc': data.get('fc', 0),
            'spo2': data.get('spo2', 0),
            'temp': data.get('temp', 0.0),
            'state': data.get('state', 'SIN_DEDO'),
            'timestamp': data.get('timestamp', datetime.now().isoformat())
        })
        
        # Actualizar buffers
        self.fc_buffer.append(data.get('fc', 0))
        self.spo2_buffer.append(data.get('spo2', 0))
        self.temp_buffer.append(data.get('temp', 0.0))
        self.timestamps.append(
            datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat()))
            .strftime('%H:%M:%S')
        )
        
        # Detectar alertas
        self._check_alerts(data)
    
    def _check_alerts(self, data):
        """Detecta y registra alertas"""
        fc = data.get('fc', 0)
        spo2 = data.get('spo2', 0)
        state = data.get('state', 'NORMAL')
        
        alert = None
        
        if state == 'STRESS':
            alert = {
                'type': 'stress',
                'message': f'Estrés detectado - FC: {fc} bpm',
                'severity': 'warning',
                'timestamp': datetime.now().isoformat()
            }
        elif spo2 > 0 and spo2 < 90:
            alert = {
                'type': 'low_spo2',
                'message': f'SpO2 bajo - {spo2}%',
                'severity': 'danger',
                'timestamp': datetime.now().isoformat()
            }
        elif fc > 120:
            alert = {
                'type': 'high_hr',
                'message': f'Frecuencia cardíaca alta - {fc} bpm',
                'severity': 'warning',
                'timestamp': datetime.now().isoformat()
            }
        
        if alert:
            self.alerts.append(alert)
            return alert
        return None
    
    def get_current(self):
        """Obtiene datos actuales con buffers"""
        return {
            **self.current_data,
            'buffers': {
                'fc': list(self.fc_buffer),
                'spo2': list(self.spo2_buffer),
                'temp': list(self.temp_buffer),
                'timestamps': list(self.timestamps)
            }
        }
    
    def register_gateway(self, gateway_id, info):
        """Registra un nuevo gateway"""
        self.gateways[gateway_id] = info
        self.gateway_last_seen[gateway_id] = datetime.now()
        logger.info(f"✓ Gateway registrado: {gateway_id}")
    
    def update_gateway_ping(self, gateway_id):
        """Actualiza último ping de gateway"""
        self.gateway_last_seen[gateway_id] = datetime.now()

# Instancia global del data store
data_store = DataStore()

# Clave secreta para autenticar gateways
GATEWAY_SECRET = os.getenv('GATEWAY_SECRET_KEY', 'default-secret-change-me')

def verify_gateway_auth():
    """Verifica que la petición viene de un gateway autorizado"""
    secret = request.headers.get('X-Gateway-Secret')
    if secret != GATEWAY_SECRET:
        logger.warning(f"Intento de acceso no autorizado desde {request.remote_addr}")
        return False
    return True


# ==================== RUTAS PÚBLICAS (WEB) ====================

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')


@app.route('/api/status', methods=['GET'])
def get_status():
    """Obtiene el estado actual del sistema"""
    try:
        data = data_store.get_current()
        
        # Verificar si hay gateways conectados
        connected_gateways = 0
        for gateway_id, last_seen in data_store.gateway_last_seen.items():
            if datetime.now() - last_seen < timedelta(minutes=2):
                connected_gateways += 1
        
        return jsonify({
            'success': True,
            'connected': connected_gateways > 0,
            'gateways_connected': connected_gateways,
            'data': data
        })
    except Exception as e:
        logger.error(f"Error en /api/status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Obtiene alertas recientes"""
    try:
        return jsonify({
            'success': True,
            'alerts': list(data_store.alerts)
        })
    except Exception as e:
        logger.error(f"Error en /api/alerts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ai_tips', methods=['POST'])
def ai_tips():
    """Genera consejos de IA basados en datos biométricos"""
    if not ai_service:
        return jsonify({
            'success': False,
            'error': 'Servicio de IA no disponible'
        }), 503
    
    try:
        data = request.get_json()
        
        fc = data.get('fc', 0)
        spo2 = data.get('spo2', 0)
        temp = data.get('temp', 0)
        state = data.get('state', 'NORMAL')
        
        result = ai_service.get_stress_tips(fc, spo2, temp, state)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error en /api/ai_tips: {e}")
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor'
        }), 500


# ==================== RUTAS DE GATEWAY (AUTENTICADAS) ====================

@app.route('/api/gateway/register', methods=['POST'])
def gateway_register():
    """Endpoint para que gateways se registren"""
    if not verify_gateway_auth():
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    
    try:
        data = request.get_json()
        gateway_id = data.get('gateway_id')
        
        if not gateway_id:
            return jsonify({'success': False, 'error': 'gateway_id requerido'}), 400
        
        data_store.register_gateway(gateway_id, data)
        
        return jsonify({
            'success': True,
            'message': f'Gateway {gateway_id} registrado',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en /api/gateway/register: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/gateway/ping', methods=['GET'])
def gateway_ping():
    """Endpoint de ping para gateways"""
    if not verify_gateway_auth():
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    
    gateway_id = request.args.get('gateway_id')
    if gateway_id:
        data_store.update_gateway_ping(gateway_id)
    
    return jsonify({
        'success': True,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/gateway/data', methods=['POST'])
def gateway_data():
    """Endpoint para recibir datos del gateway"""
    if not verify_gateway_auth():
        return jsonify({'success': False, 'error': 'No autorizado'}), 401
    
    try:
        data = request.get_json()
        
        # Actualizar data store
        data_store.update(data)
        
        # Emitir a todos los clientes conectados vía WebSocket
        socketio.emit('nuevos_datos', data_store.get_current(), namespace='/')
        
        # Verificar si hay alerta
        alert = data_store._check_alerts(data)
        if alert:
            socketio.emit('nueva_alerta', alert, namespace='/')
        
        return jsonify({
            'success': True,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error en /api/gateway/data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== WEBSOCKET HANDLERS ====================

@socketio.on('connect')
def handle_connect():
    """Cliente conectado vía WebSocket"""
    logger.info(f"Cliente web conectado: {request.sid}")
    # Enviar datos actuales al nuevo cliente
    emit('nuevos_datos', data_store.get_current())


@socketio.on('disconnect')
def handle_disconnect():
    """Cliente desconectado"""
    logger.info(f"Cliente web desconectado: {request.sid}")


@socketio.on('request_data')
def handle_request_data():
    """Cliente solicita datos actuales"""
    emit('nuevos_datos', data_store.get_current())


# ==================== HEALTH CHECK ====================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check para el deployment"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'gateways': len(data_store.gateways)
    })


if __name__ == '__main__':
    logger.info("\n" + "=" * 60)
    logger.info("  FILSYNC CLOUD SERVER")
    logger.info("  Servidor web en la nube")
    logger.info("=" * 60)
    logger.info(f"\n🌐 Puerto: {os.getenv('PORT', 8000)}")
    logger.info(f"🔑 Auth configurada: {'✓' if GATEWAY_SECRET != 'default-secret-change-me' else '⚠️  Usar SECRET por defecto'}")
    logger.info(f"🤖 IA disponible: {'✓' if ai_service else '❌'}\n")
    logger.info("=" * 60 + "\n")
    
    port = int(os.getenv('PORT', 8000))
    
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=False,
        use_reloader=False
    )
