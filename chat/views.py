import json
import random
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from .models import PhoneVerification, ICEChatSession, ICEChatMessage

# URL del agente externo
AGENT_URL = 'https://behemotmalaki-production.up.railway.app'


def generate_code():
    """Genera un código de 6 dígitos"""
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])


def send_sms_twilio(phone, message):
    """Envía SMS usando Twilio"""
    try:
        from twilio.rest import Client

        account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        from_phone = getattr(settings, 'TWILIO_PHONE_NUMBER', None)

        if not all([account_sid, auth_token, from_phone]):
            print("Twilio no configurado. Código:", message)
            return True  # En desarrollo, simula éxito

        client = Client(account_sid, auth_token)
        client.messages.create(
            body=message,
            from_=from_phone,
            to=phone
        )
        return True
    except Exception as e:
        print(f"Error enviando SMS: {e}")
        return False


@csrf_exempt
@require_http_methods(["POST"])
def send_verification_code(request):
    """Envía código de verificación por SMS"""
    try:
        data = json.loads(request.body)
        phone = data.get('phone', '').strip()

        if not phone:
            return JsonResponse({'success': False, 'error': 'Número de teléfono requerido'}, status=400)

        # Verificar límite de intentos (máximo 3 códigos en 1 hora)
        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_codes = PhoneVerification.objects.filter(
            phone=phone,
            created_at__gte=one_hour_ago
        ).count()

        if recent_codes >= 3:
            return JsonResponse({
                'success': False,
                'error': 'Demasiados intentos. Espera 1 hora.'
            }, status=429)

        # Generar código
        code = generate_code()

        # Guardar verificación
        verification = PhoneVerification.objects.create(
            phone=phone,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        # Enviar SMS
        message = f"ICE Asunción: Tu código de verificación es {code}. Válido por 10 minutos."
        sms_sent = send_sms_twilio(phone, message)

        if sms_sent:
            return JsonResponse({
                'success': True,
                'message': 'Código enviado correctamente'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Error enviando SMS. Intenta de nuevo.'
            }, status=500)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def verify_code(request):
    """Verifica el código y crea una sesión de chat"""
    try:
        data = json.loads(request.body)
        phone = data.get('phone', '').strip()
        code = data.get('code', '').strip()

        if not phone or not code:
            return JsonResponse({
                'success': False,
                'error': 'Teléfono y código son requeridos'
            }, status=400)

        # Buscar verificación válida
        verification = PhoneVerification.objects.filter(
            phone=phone,
            code=code,
            verified=False
        ).order_by('-created_at').first()

        if not verification:
            return JsonResponse({
                'success': False,
                'error': 'Código inválido'
            }, status=400)

        # Verificar expiración
        if verification.is_expired():
            return JsonResponse({
                'success': False,
                'error': 'El código ha expirado'
            }, status=400)

        # Verificar intentos
        verification.attempts += 1
        if verification.attempts > 5:
            return JsonResponse({
                'success': False,
                'error': 'Demasiados intentos. Solicita un nuevo código.'
            }, status=429)
        verification.save()

        # Marcar como verificado
        verification.verified = True
        verification.save()

        # Buscar sesión existente o crear una nueva
        session = ICEChatSession.objects.filter(
            phone=phone,
            is_active=True
        ).order_by('-updated_at').first()

        if not session:
            session = ICEChatSession.objects.create(phone=phone)

        return JsonResponse({
            'success': True,
            'session_id': str(session.session_id),
            'message': 'Verificación exitosa'
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def send_message(request):
    """Envía un mensaje de texto al agente"""
    try:
        data = json.loads(request.body)
        session_id = data.get('session_id', '').strip()
        message = data.get('message', '').strip()

        if not session_id or not message:
            return JsonResponse({
                'success': False,
                'error': 'session_id y mensaje son requeridos'
            }, status=400)

        # Verificar sesión
        try:
            session = ICEChatSession.objects.get(session_id=session_id, is_active=True)
        except ICEChatSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Sesión inválida o expirada'
            }, status=401)

        # Guardar mensaje del usuario
        ICEChatMessage.objects.create(
            session=session,
            role='user',
            message_type='text',
            content=message
        )

        # Enviar al agente externo
        try:
            agent_response = requests.post(
                f'{AGENT_URL}/api/chat',
                json={
                    'message': message,
                    'thread_id': session.agent_thread_id or None
                },
                timeout=60
            )

            if agent_response.status_code == 200:
                response_data = agent_response.json()
                assistant_message = response_data.get('response', response_data.get('message', ''))
                thread_id = response_data.get('thread_id', '')

                # Actualizar thread_id si es nuevo
                if thread_id and not session.agent_thread_id:
                    session.agent_thread_id = thread_id
                    session.save()

                # Guardar respuesta del asistente
                ICEChatMessage.objects.create(
                    session=session,
                    role='assistant',
                    message_type='text',
                    content=assistant_message
                )

                # Actualizar sesión
                session.save()  # Actualiza updated_at

                return JsonResponse({
                    'success': True,
                    'response': assistant_message
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Error al comunicarse con el agente'
                }, status=502)

        except requests.Timeout:
            return JsonResponse({
                'success': False,
                'error': 'El agente tardó demasiado en responder'
            }, status=504)
        except requests.RequestException as e:
            return JsonResponse({
                'success': False,
                'error': f'Error de conexión: {str(e)}'
            }, status=502)

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def send_audio(request):
    """Envía un mensaje de audio al agente"""
    try:
        session_id = request.POST.get('session_id', '').strip()
        audio_file = request.FILES.get('audio')

        if not session_id or not audio_file:
            return JsonResponse({
                'success': False,
                'error': 'session_id y audio son requeridos'
            }, status=400)

        # Verificar sesión
        try:
            session = ICEChatSession.objects.get(session_id=session_id, is_active=True)
        except ICEChatSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Sesión inválida o expirada'
            }, status=401)

        # Enviar audio al agente externo
        try:
            files = {'audio': (audio_file.name, audio_file, audio_file.content_type)}
            data = {'thread_id': session.agent_thread_id or ''}

            agent_response = requests.post(
                f'{AGENT_URL}/api/chat/audio',
                files=files,
                data=data,
                timeout=120
            )

            if agent_response.status_code == 200:
                response_data = agent_response.json()

                # Obtener transcripción del usuario (si está disponible)
                user_transcription = response_data.get('transcription', '[Audio]')
                assistant_message = response_data.get('response', response_data.get('message', ''))
                thread_id = response_data.get('thread_id', '')

                # Actualizar thread_id si es nuevo
                if thread_id and not session.agent_thread_id:
                    session.agent_thread_id = thread_id
                    session.save()

                # Guardar mensaje del usuario
                ICEChatMessage.objects.create(
                    session=session,
                    role='user',
                    message_type='audio',
                    content=user_transcription
                )

                # Guardar respuesta del asistente
                ICEChatMessage.objects.create(
                    session=session,
                    role='assistant',
                    message_type='text',
                    content=assistant_message
                )

                # Actualizar sesión
                session.save()

                return JsonResponse({
                    'success': True,
                    'transcription': user_transcription,
                    'response': assistant_message
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Error al procesar el audio'
                }, status=502)

        except requests.Timeout:
            return JsonResponse({
                'success': False,
                'error': 'El procesamiento del audio tardó demasiado'
            }, status=504)
        except requests.RequestException as e:
            return JsonResponse({
                'success': False,
                'error': f'Error de conexión: {str(e)}'
            }, status=502)

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_history(request, session_id):
    """Obtiene el historial de chat de una sesión"""
    try:
        # Verificar sesión
        try:
            session = ICEChatSession.objects.get(session_id=session_id)
        except ICEChatSession.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Sesión no encontrada'
            }, status=404)

        # Obtener mensajes
        messages = session.messages.all().values(
            'role', 'message_type', 'content', 'created_at'
        )

        return JsonResponse({
            'success': True,
            'messages': list(messages)
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
