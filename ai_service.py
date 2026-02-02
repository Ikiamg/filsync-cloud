import requests
import logging
import os

logger = logging.getLogger(__name__)


class AIService:
    """Servicio para interactuar con OpenRouter API"""

    def __init__(self):
        self.api_key = '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'
        self.base_url = 'https://openrouter.ai/api/v1/chat/completions'
        self.model = 'openai/gpt-oss-120b:free'

        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY no configurada")

    def get_stress_tips(self, fc, spo2, temp, state):
        """
        Genera consejos para manejar el estrés basado en datos biométricos

        Args:
            fc: Frecuencia cardíaca
            spo2: Saturación de oxígeno
            temp: Temperatura corporal
            state: Estado actual (RELAX/NORMAL/STRESS/SIN_DEDO)

        Returns:
            dict: {'success': bool, 'tips': str, 'error': str}
        """

        # Validaciones
        if not self.api_key:
            return {
                'success': False,
                'error': 'API key no configurada',
                'tips': ''
            }

        if state == "SIN_DEDO" or fc == 0:
            return {
                'success': False,
                'error': 'No hay datos de sensor válidos',
                'tips': ''
            }

        if state != "STRESS":
            return {
                'success': True,
                'tips': 'Tus signos vitales están en rangos normales. Continúa así.',
                'error': ''
            }

        # Construir prompt
        prompt = f"""Eres un asistente de bienestar personal. Un usuario tiene los siguientes datos biométricos:

- Frecuencia cardíaca: {fc} bpm
- Saturación de oxígeno: {spo2}%
- Temperatura: {temp}°C
- Estado: ESTRÉS DETECTADO

Proporciona 3-4 consejos BREVES y PRÁCTICOS para ayudar a reducir el estrés de forma inmediata. Los consejos deben ser:

1. Técnicas de respiración simples
2. Pausas activas o estiramientos rápidos
3. Hidratación o bienestar general
4. Cambios en el entorno inmediato

IMPORTANTE:
- NO proporciones diagnósticos médicos
- NO recomiendes medicamentos
- Mantén los consejos concretos y accionables
- Máximo 150 palabras en total
- Usa un tono amigable y motivador

Formato: Lista numerada simple."""

        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://github.com/biometric-monitor',
                'X-Title': 'Biometric Monitor'
            }

            payload = {
                'model': self.model,
                'messages': [
                    {
                        'role': 'system',
                        'content': 'Eres un asistente de bienestar que proporciona consejos prácticos para reducir el estrés. NUNCA das diagnósticos médicos ni recomiendas medicamentos.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'max_tokens': 300,
                'temperature': 0.7
            }

            logger.info(f"Solicitando consejos de IA (FC: {fc}, Estado: {state})")

            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            response.raise_for_status()
            data = response.json()

            if 'choices' in data and len(data['choices']) > 0:
                tips = data['choices'][0]['message']['content'].strip()

                logger.info("Consejos de IA generados exitosamente")

                return {
                    'success': True,
                    'tips': tips,
                    'error': ''
                }
            else:
                logger.error(f"Respuesta inesperada de API: {data}")
                return {
                    'success': False,
                    'error': 'Respuesta inválida de la API',
                    'tips': ''
                }

        except requests.exceptions.Timeout:
            logger.error("Timeout al conectar con OpenRouter")
            return {
                'success': False,
                'error': 'La solicitud tardó demasiado. Intenta nuevamente.',
                'tips': ''
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Error en solicitud a OpenRouter: {e}")
            logger.error(f"Status code: {getattr(e.response, 'status_code', 'N/A') if hasattr(e, 'response') else 'N/A'}")
            logger.error(f"Response text: {getattr(e.response, 'text', 'N/A') if hasattr(e, 'response') else 'N/A'}")
            
            error_msg = 'Error de conexión con el servicio de IA'
            if hasattr(e, 'response') and e.response is not None:
                if e.response.status_code == 401:
                    error_msg = 'API key inválida o expirada'
                elif e.response.status_code == 429:
                    error_msg = 'Límite de peticiones excedido. Intenta en unos minutos'
                elif e.response.status_code >= 500:
                    error_msg = 'Error en el servidor de IA. Intenta nuevamente'
            
            return {
                'success': False,
                'error': error_msg,
                'tips': ''
            }


        except Exception as e:
            logger.error(f"Error inesperado en AI Service: {e}", exc_info=True)
            return {
                'success': False,
                'error': 'Error interno del servidor',
                'tips': ''
            }

    def chat(self, message, context=None):
        """
        Chat conversacional con el usuario

        Args:
            message: Mensaje del usuario
            context: Lista de mensajes previos [{'role': 'user/assistant', 'content': '...'}]

        Returns:
            dict: {'success': bool, 'response': str, 'error': str}
        """

        if not self.api_key:
            return {
                'success': False,
                'error': 'API key no configurada',
                'response': ''
            }

        if not message or len(message.strip()) == 0:
            return {
                'success': False,
                'error': 'Mensaje vacío',
                'response': ''
            }

        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://github.com/biometric-monitor',
                'X-Title': 'Biometric Monitor'
            }

            # Construir historial de mensajes
            messages = [
                {
                    'role': 'system',
                    'content': '''Eres un asistente amigable de un sistema de monitoreo biométrico. 
                    Ayudas a los usuarios con preguntas sobre salud y bienestar general.

                    REGLAS ESTRICTAS:
                    - NUNCA proporciones diagnósticos médicos
                    - NUNCA recomiendes medicamentos específicos
                    - Si el usuario pregunta sobre síntomas graves, recomienda consultar a un profesional
                    - Mantén respuestas concisas (máximo 100 palabras)
                    - Usa un tono amigable y motivador'''
                }
            ]

            # Añadir contexto si existe (máximo 5 mensajes previos)
            if context and isinstance(context, list):
                messages.extend(context[-5:])

            # Añadir mensaje actual
            messages.append({
                'role': 'user',
                'content': message
            })

            payload = {
                'model': self.model,
                'messages': messages,
                'max_tokens': 200,
                'temperature': 0.8
            }

            logger.info(f"Chat request: {message[:50]}...")

            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            response.raise_for_status()
            data = response.json()

            if 'choices' in data and len(data['choices']) > 0:
                ai_response = data['choices'][0]['message']['content'].strip()

                logger.info("Respuesta de chat generada")

                return {
                    'success': True,
                    'response': ai_response,
                    'error': ''
                }
            else:
                logger.error(f"Respuesta inesperada: {data}")
                return {
                    'success': False,
                    'error': 'Respuesta inválida de la API',
                    'response': ''
                }

        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Timeout',
                'response': ''
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Error en chat: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': ''
            }

        except Exception as e:
            logger.error(f"Error inesperado en chat: {e}", exc_info=True)
            return {
                'success': False,
                'error': 'Error interno',
                'response': ''
            }


