/**
 * Chat Widget ICE Asunción
 * Widget de chat con verificación SMS y soporte de texto/audio
 */

(function() {
    'use strict';

    // Configuración
    const CONFIG = {
        API_BASE: '/chat/api',
        SESSION_KEY: 'ice_chat_session',
        PHONE_KEY: 'ice_chat_phone'
    };

    // Estado del chat
    let state = {
        isOpen: false,
        isVerified: false,
        sessionId: null,
        phone: null,
        isRecording: false,
        mediaRecorder: null,
        audioChunks: []
    };

    // Elementos DOM
    let elements = {};

    /**
     * Inicialización
     */
    function init() {
        // Obtener elementos DOM
        elements = {
            widget: document.getElementById('ice-chat-widget'),
            fab: document.getElementById('ice-chat-fab'),
            container: document.getElementById('ice-chat-container'),
            closeBtn: document.getElementById('ice-chat-close'),
            // Verificación
            verifyView: document.getElementById('ice-chat-verify'),
            verifyStep1: document.getElementById('ice-verify-step1'),
            verifyStep2: document.getElementById('ice-verify-step2'),
            phoneInput: document.getElementById('ice-phone-input'),
            codeInput: document.getElementById('ice-code-input'),
            sendCodeBtn: document.getElementById('ice-send-code-btn'),
            verifyCodeBtn: document.getElementById('ice-verify-code-btn'),
            resendCodeBtn: document.getElementById('ice-resend-code-btn'),
            verifyMessage: document.getElementById('ice-verify-message'),
            // Chat principal
            mainView: document.getElementById('ice-chat-main'),
            messagesContainer: document.getElementById('ice-chat-messages'),
            chatInput: document.getElementById('ice-chat-input'),
            sendBtn: document.getElementById('ice-send-btn'),
            audioBtn: document.getElementById('ice-audio-btn'),
            recordingIndicator: document.getElementById('ice-recording-indicator'),
            stopRecordingBtn: document.getElementById('ice-stop-recording'),
            loadingIndicator: document.getElementById('ice-chat-loading')
        };

        // Verificar si hay sesión guardada
        checkExistingSession();

        // Event listeners
        setupEventListeners();
    }

    /**
     * Configurar event listeners
     */
    function setupEventListeners() {
        // Abrir/cerrar chat
        elements.fab.addEventListener('click', toggleChat);
        elements.closeBtn.addEventListener('click', closeChat);

        // Verificación
        elements.sendCodeBtn.addEventListener('click', sendVerificationCode);
        elements.verifyCodeBtn.addEventListener('click', verifyCode);
        elements.resendCodeBtn.addEventListener('click', sendVerificationCode);

        // Chat
        elements.sendBtn.addEventListener('click', sendMessage);
        elements.chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });

        // Auto-resize textarea
        elements.chatInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 100) + 'px';
        });

        // Audio
        elements.audioBtn.addEventListener('click', toggleRecording);
        elements.stopRecordingBtn.addEventListener('click', stopRecording);

        // Enter en inputs de verificación
        elements.phoneInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendVerificationCode();
        });
        elements.codeInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') verifyCode();
        });
    }

    /**
     * Verificar sesión existente
     */
    function checkExistingSession() {
        const sessionId = localStorage.getItem(CONFIG.SESSION_KEY);
        const phone = localStorage.getItem(CONFIG.PHONE_KEY);

        if (sessionId && phone) {
            state.sessionId = sessionId;
            state.phone = phone;
            state.isVerified = true;
            showChatView();
            loadChatHistory();
        }
    }

    /**
     * Abrir/cerrar chat
     */
    function toggleChat() {
        if (state.isOpen) {
            closeChat();
        } else {
            openChat();
        }
    }

    function openChat() {
        state.isOpen = true;
        elements.container.classList.add('ice-chat-open');
        elements.fab.innerHTML = '<i class="bi bi-x-lg"></i>';

        if (state.isVerified) {
            elements.chatInput.focus();
        } else {
            elements.phoneInput.focus();
        }
    }

    function closeChat() {
        state.isOpen = false;
        elements.container.classList.remove('ice-chat-open');
        elements.fab.innerHTML = '<i class="bi bi-chat-dots-fill"></i>';
    }

    /**
     * Enviar código de verificación
     */
    async function sendVerificationCode() {
        const phone = elements.phoneInput.value.trim();

        if (!phone) {
            showVerifyMessage('Por favor ingresa tu número de teléfono', 'error');
            return;
        }

        setLoading(true, elements.sendCodeBtn, 'Enviando...');

        try {
            const response = await fetch(`${CONFIG.API_BASE}/send-code/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ phone: phone })
            });

            const data = await response.json();

            if (data.success) {
                state.phone = phone;
                elements.verifyStep1.classList.add('d-none');
                elements.verifyStep2.classList.remove('d-none');
                elements.codeInput.focus();
                showVerifyMessage('Código enviado correctamente', 'success');
            } else {
                showVerifyMessage(data.error || 'Error al enviar el código', 'error');
            }
        } catch (error) {
            showVerifyMessage('Error de conexión. Intenta de nuevo.', 'error');
        } finally {
            setLoading(false, elements.sendCodeBtn, '<i class="bi bi-send"></i> Enviar código');
        }
    }

    /**
     * Verificar código
     */
    async function verifyCode() {
        const code = elements.codeInput.value.trim();

        if (!code || code.length !== 6) {
            showVerifyMessage('Por favor ingresa el código de 6 dígitos', 'error');
            return;
        }

        setLoading(true, elements.verifyCodeBtn, 'Verificando...');

        try {
            const response = await fetch(`${CONFIG.API_BASE}/verify-code/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    phone: state.phone,
                    code: code
                })
            });

            const data = await response.json();

            if (data.success) {
                state.sessionId = data.session_id;
                state.isVerified = true;

                // Guardar sesión
                localStorage.setItem(CONFIG.SESSION_KEY, state.sessionId);
                localStorage.setItem(CONFIG.PHONE_KEY, state.phone);

                showChatView();
            } else {
                showVerifyMessage(data.error || 'Código inválido', 'error');
            }
        } catch (error) {
            showVerifyMessage('Error de conexión. Intenta de nuevo.', 'error');
        } finally {
            setLoading(false, elements.verifyCodeBtn, '<i class="bi bi-check-circle"></i> Verificar');
        }
    }

    /**
     * Mostrar vista del chat
     */
    function showChatView() {
        elements.verifyView.classList.add('d-none');
        elements.mainView.classList.remove('ice-chat-main-hidden');
        elements.chatInput.focus();
    }

    /**
     * Cargar historial del chat
     */
    async function loadChatHistory() {
        try {
            const response = await fetch(`${CONFIG.API_BASE}/history/${state.sessionId}/`);
            const data = await response.json();

            if (data.success && data.messages.length > 0) {
                // Limpiar mensaje de bienvenida si hay historial
                const welcomeMsg = elements.messagesContainer.querySelector('.ice-chat-welcome');
                if (welcomeMsg && data.messages.length > 0) {
                    welcomeMsg.style.display = 'none';
                }

                data.messages.forEach(msg => {
                    addMessageToUI(msg.content, msg.role, false);
                });

                // Scroll al final después de cargar el historial
                setTimeout(() => {
                    elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
                }, 100);
            }
        } catch (error) {
            console.error('Error cargando historial:', error);
        }
    }

    /**
     * Enviar mensaje de texto
     */
    async function sendMessage() {
        const message = elements.chatInput.value.trim();

        if (!message) return;

        // Agregar mensaje del usuario a la UI
        addMessageToUI(message, 'user');

        // Limpiar input
        elements.chatInput.value = '';
        elements.chatInput.style.height = 'auto';

        // Mostrar indicador de escritura
        showTypingIndicator();

        try {
            const response = await fetch(`${CONFIG.API_BASE}/send-message/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    session_id: state.sessionId,
                    message: message
                })
            });

            const data = await response.json();
            hideTypingIndicator();

            if (data.success) {
                addMessageToUI(data.response, 'assistant');
            } else {
                addMessageToUI('Lo siento, hubo un error. Por favor intenta de nuevo.', 'assistant');
            }
        } catch (error) {
            hideTypingIndicator();
            addMessageToUI('Error de conexión. Por favor intenta de nuevo.', 'assistant');
        }
    }

    /**
     * Grabar y enviar audio
     */
    async function toggleRecording() {
        if (state.isRecording) {
            stopRecording();
        } else {
            startRecording();
        }
    }

    async function startRecording() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

            state.mediaRecorder = new MediaRecorder(stream);
            state.audioChunks = [];

            state.mediaRecorder.ondataavailable = (event) => {
                state.audioChunks.push(event.data);
            };

            state.mediaRecorder.onstop = async () => {
                const audioBlob = new Blob(state.audioChunks, { type: 'audio/webm' });
                await sendAudio(audioBlob);

                // Detener el stream
                stream.getTracks().forEach(track => track.stop());
            };

            state.mediaRecorder.start();
            state.isRecording = true;

            // Actualizar UI
            elements.audioBtn.innerHTML = '<i class="bi bi-stop-fill"></i>';
            elements.audioBtn.classList.add('text-danger');
            elements.recordingIndicator.classList.remove('d-none');

        } catch (error) {
            console.error('Error al acceder al micrófono:', error);
            alert('No se pudo acceder al micrófono. Por favor verifica los permisos.');
        }
    }

    function stopRecording() {
        if (state.mediaRecorder && state.isRecording) {
            state.mediaRecorder.stop();
            state.isRecording = false;

            // Actualizar UI
            elements.audioBtn.innerHTML = '<i class="bi bi-mic"></i>';
            elements.audioBtn.classList.remove('text-danger');
            elements.recordingIndicator.classList.add('d-none');
        }
    }

    async function sendAudio(audioBlob) {
        // Mostrar mensaje de audio del usuario
        addMessageToUI('[Mensaje de audio]', 'user', true, true);

        // Mostrar indicador de escritura
        showTypingIndicator();

        try {
            const formData = new FormData();
            formData.append('session_id', state.sessionId);
            formData.append('audio_file', audioBlob, 'audio.webm');

            const response = await fetch(`${CONFIG.API_BASE}/send-audio/`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();
            hideTypingIndicator();

            if (data.success) {
                // Actualizar mensaje del usuario con la transcripción
                if (data.transcription) {
                    updateLastUserMessage(data.transcription);
                }
                addMessageToUI(data.response, 'assistant');
            } else {
                addMessageToUI('Lo siento, no pude procesar el audio. Por favor intenta de nuevo.', 'assistant');
            }
        } catch (error) {
            hideTypingIndicator();
            addMessageToUI('Error al enviar el audio. Por favor intenta de nuevo.', 'assistant');
        }
    }

    /**
     * Agregar mensaje a la UI
     */
    function addMessageToUI(content, role, animate = true, isAudio = false) {
        // Ocultar mensaje de bienvenida
        const welcomeMsg = elements.messagesContainer.querySelector('.ice-chat-welcome');
        if (welcomeMsg) {
            welcomeMsg.style.display = 'none';
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `ice-chat-message ${role}`;
        if (!animate) messageDiv.style.animation = 'none';

        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = 'ice-chat-bubble';

        if (isAudio) {
            bubbleDiv.innerHTML = `
                <div class="ice-chat-audio-indicator">
                    <i class="bi bi-mic-fill"></i>
                    <span>${content}</span>
                </div>
            `;
        } else if (role === 'assistant' && typeof marked !== 'undefined') {
            // Parsear markdown para mensajes del asistente
            bubbleDiv.innerHTML = marked.parse(content);
            bubbleDiv.classList.add('ice-chat-markdown');
        } else {
            bubbleDiv.textContent = content;
        }

        messageDiv.appendChild(bubbleDiv);
        elements.messagesContainer.appendChild(messageDiv);

        // Scroll al final
        elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
    }

    /**
     * Actualizar último mensaje del usuario (para transcripción de audio)
     */
    function updateLastUserMessage(text) {
        const userMessages = elements.messagesContainer.querySelectorAll('.ice-chat-message.user');
        if (userMessages.length > 0) {
            const lastMessage = userMessages[userMessages.length - 1];
            const bubble = lastMessage.querySelector('.ice-chat-bubble');
            if (bubble) {
                bubble.innerHTML = `
                    <div class="ice-chat-audio-indicator">
                        <i class="bi bi-mic-fill"></i>
                        <span>${text}</span>
                    </div>
                `;
            }
        }
    }

    /**
     * Indicador de escritura
     */
    function showTypingIndicator() {
        const typingDiv = document.createElement('div');
        typingDiv.id = 'ice-typing-indicator';
        typingDiv.className = 'ice-chat-message assistant';
        typingDiv.innerHTML = `
            <div class="ice-chat-typing">
                <span></span>
                <span></span>
                <span></span>
            </div>
        `;
        elements.messagesContainer.appendChild(typingDiv);
        elements.messagesContainer.scrollTop = elements.messagesContainer.scrollHeight;
    }

    function hideTypingIndicator() {
        const typingIndicator = document.getElementById('ice-typing-indicator');
        if (typingIndicator) {
            typingIndicator.remove();
        }
    }

    /**
     * Mostrar mensaje en verificación
     */
    function showVerifyMessage(message, type) {
        elements.verifyMessage.className = `mt-3 ice-chat-alert ${type}`;
        elements.verifyMessage.textContent = message;
        elements.verifyMessage.classList.remove('d-none');

        setTimeout(() => {
            elements.verifyMessage.classList.add('d-none');
        }, 5000);
    }

    /**
     * Estado de carga en botones
     */
    function setLoading(isLoading, button, text) {
        if (isLoading) {
            button.disabled = true;
            button.innerHTML = `<span class="spinner-border spinner-border-sm me-2"></span>${text}`;
        } else {
            button.disabled = false;
            button.innerHTML = text;
        }
    }

    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
