// Configuración global
const CONFIG = {
    maxDataPoints: 50,
    chartUpdateInterval: 1000,
    tipsDebounceTime: 5000
};

// Estado global
let socket = null;
let charts = {};
let lastStressTime = 0;
let tipsShown = false;

// Elementos del DOM
const elements = {
    connectionStatus: document.getElementById('connectionStatus'),
    stateCard: document.getElementById('stateCard'),
    stateIcon: document.getElementById('stateIcon'),
    stateTitle: document.getElementById('stateTitle'),
    fcValue: document.getElementById('fcValue'),
    spo2Value: document.getElementById('spo2Value'),
    aiTips: document.getElementById('aiTips'),
    tipsContent: document.getElementById('tipsContent'),
    chatMessages: document.getElementById('chatMessages'),
    chatInput: document.getElementById('chatInput'),
    sendBtn: document.getElementById('sendBtn'),
    clearChatBtn: document.getElementById('clearChatBtn')
};

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    console.log(' Iniciando aplicación...');
    initializeCharts();
    initializeWebSocket();
    initializeChatHandlers();
});

// ============================================
// WebSocket
// ============================================

function initializeWebSocket() {
    console.log(' Conectando al servidor WebSocket...');

    socket = io({
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionAttempts: Infinity
    });

    socket.on('connect', () => {
        console.log(' Conectado al servidor');
        updateConnectionStatus(true);
        socket.emit('request_data');
    });

    socket.on('disconnect', () => {
        console.log(' Desconectado del servidor');
        updateConnectionStatus(false);
    });

    socket.on('nuevos_datos', (data) => {
        console.log(' Nuevos datos recibidos:', data);
        updateUI(data);
    });

    socket.on('connect_error', (error) => {
        console.error('Error de conexión:', error);
        updateConnectionStatus(false);
    });
}

function updateConnectionStatus(connected) {
    const statusDot = elements.connectionStatus.querySelector('.status-dot');
    const statusText = elements.connectionStatus.querySelector('.status-text');

    if (connected) {
        statusDot.classList.remove('disconnected');
        statusDot.classList.add('connected');
        statusText.textContent = 'Conectado';
    } else {
        statusDot.classList.remove('connected');
        statusDot.classList.add('disconnected');
        statusText.textContent = 'Desconectado';
    }
}

// ============================================
// Actualización de UI
// ============================================

function updateUI(data) {
    // Actualizar valores numéricos
    elements.fcValue.textContent = data.fc || '--';
    elements.spo2Value.textContent = data.spo2 || '--';

    // Actualizar estado
    updateState(data.state || 'SIN_DEDO');

    // Actualizar gráficas
    if (data.buffers) {
        updateCharts(data.buffers);
    }

    // Verificar si mostrar consejos de IA
    checkAndShowAITips(data);
}

function updateState(state) {
    // Remover clases anteriores
    elements.stateCard.classList.remove('relax', 'normal', 'stress', 'no-finger');

    // Configuración según estado
    const stateConfig = {
        'RELAX': {
            class: 'relax',
            icon: 'fa-smile',
            title: 'RELAJADO',
            subtitle: 'Tu ritmo cardíaco está bajo. ¡Sigue así!'
        },
        'NORMAL': {
            class: 'normal',
            icon: 'fa-heart',
            title: 'NORMAL',
            subtitle: 'Tus signos vitales están en rango normal'
        },
        'STRESS': {
            class: 'stress',
            icon: 'fa-exclamation-triangle',
            title: 'ESTRÉS DETECTADO',
            subtitle: 'Tu ritmo cardíaco está elevado. Considera tomar un descanso'
        },
        'SIN_DEDO': {
            class: 'no-finger',
            icon: 'fa-hand-paper',
            title: 'SIN DEDO',
            subtitle: 'Coloque el dedo en el sensor'
        }
    };

    const config = stateConfig[state] || stateConfig['SIN_DEDO'];

    elements.stateCard.classList.add(config.class);
    elements.stateIcon.innerHTML = `<i class="fas ${config.icon}"></i>`;
    elements.stateTitle.textContent = config.title;
    elements.stateCard.querySelector('.state-subtitle').textContent = config.subtitle;
}

// ============================================
// Gráficas con Chart.js
// ============================================

function initializeCharts() {
    const chartConfig = (label, color, yMax) => ({
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: label,
                data: [],
                borderColor: color,
                backgroundColor: color + '20',
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 0,
                pointHoverRadius: 4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: yMax,
                    grid: { color: '#e5e7eb' }
                },
                x: {
                    grid: { display: false }
                }
            },
            animation: {
                duration: 300
            }
        }
    });

    charts.fc = new Chart(
        document.getElementById('fcChart'),
        chartConfig('FC (bpm)', '#ef4444', 120)
    );

    charts.spo2 = new Chart(
        document.getElementById('spo2Chart'),
        chartConfig('SpO2 (%)', '#3b82f6', 100)
    );


    console.log('Gráficas inicializadas');
}

function updateCharts(buffers) {
    const updateChart = (chart, data, labels) => {
        if (!data || data.length === 0) return;

        chart.data.labels = labels || buffers.timestamps || [];
        chart.data.datasets[0].data = data;

        // Mantener máximo de puntos
        if (chart.data.labels.length > CONFIG.maxDataPoints) {
            chart.data.labels = chart.data.labels.slice(-CONFIG.maxDataPoints);
            chart.data.datasets[0].data = chart.data.datasets[0].data.slice(-CONFIG.maxDataPoints);
        }

        chart.update('none'); // Sin animación para mejor rendimiento
    };

    updateChart(charts.fc, buffers.fc, buffers.timestamps);
    updateChart(charts.spo2, buffers.spo2, buffers.timestamps);
}

// ============================================
// Asistente IA - Consejos Automáticos
// ============================================

function checkAndShowAITips(data) {
    const now = Date.now();

    // Solo mostrar si está estresado y han pasado al menos 5 segundos
    if (data.state === 'STRESS' &&
        data.fc > 0 &&
        (now - lastStressTime) > CONFIG.tipsDebounceTime) {

        lastStressTime = now;
        requestAITips(data);
    } else if (data.state !== 'STRESS' && tipsShown) {
        // Ocultar consejos si ya no está estresado
        elements.aiTips.style.display = 'none';
        tipsShown = false;
    }
}

async function requestAITips(data) {
    elements.aiTips.style.display = 'block';
    elements.tipsContent.innerHTML = `
        <div class="loading">
            <i class="fas fa-spinner fa-spin"></i> Generando consejos personalizados...
        </div>
    `;
    tipsShown = true;

    try {
        const response = await fetch('/api/ai_tips', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                fc: data.fc,
                spo2: data.spo2,
                temp: data.temp,
                state: data.state
            })
        });

        const result = await response.json();

        if (result.success) {
            elements.tipsContent.innerHTML = formatTips(result.tips);
        } else {
            elements.tipsContent.innerHTML = `
                <p><i class="fas fa-exclamation-circle"></i> ${result.error || 'No se pudieron generar consejos'}</p>
            `;
        }
    } catch (error) {
        console.error('Error solicitando consejos:', error);
        elements.tipsContent.innerHTML = `
            <p><i class="fas fa-exclamation-circle"></i> Error de conexión. Intenta nuevamente.</p>
        `;
    }
}

function formatTips(tips) {
    // Convertir texto en HTML formateado
    return tips
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0)
        .map(line => {
            // Si es un item de lista numerada
            if (/^\d+\./.test(line)) {
                return `<p style="margin-bottom: 10px;">✓ ${line.substring(line.indexOf('.') + 1).trim()}</p>`;
            }
            return `<p style="margin-bottom: 8px;">${line}</p>`;
        })
        .join('');
}

// ============================================
// Chat IA
// ============================================

function initializeChatHandlers() {
    elements.sendBtn.addEventListener('click', sendMessage);

    elements.chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    elements.clearChatBtn.addEventListener('click', clearChat);
}

async function sendMessage() {
    const message = elements.chatInput.value.trim();

    if (!message) return;

    // Deshabilitar input
    elements.chatInput.disabled = true;
    elements.sendBtn.disabled = true;

    // Mostrar mensaje del usuario
    addChatMessage(message, 'user');
    elements.chatInput.value = '';

    // Mostrar indicador de escritura
    const typingId = addChatMessage('Escribiendo...', 'assistant', true);

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message })
        });

        const result = await response.json();

        // Remover indicador de escritura
        document.getElementById(typingId)?.remove();

        if (result.success) {
            addChatMessage(result.response, 'assistant');
        } else {
            addChatMessage(
                `Error: ${result.error || 'No se pudo procesar el mensaje'}`,
                'assistant'
            );
        }
    } catch (error) {
        console.error('Error en chat:', error);
        document.getElementById(typingId)?.remove();
        addChatMessage('Error de conexión. Intenta nuevamente.', 'assistant');
    } finally {
        elements.chatInput.disabled = false;
        elements.sendBtn.disabled = false;
        elements.chatInput.focus();
    }
}

function addChatMessage(text, type, isTyping = false) {
    const messageId = `msg-${Date.now()}-${Math.random()}`;
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${type}`;
    messageDiv.id = messageId;

    const icon = type === 'user' ?
        '<i class="fas fa-user"></i>' :
        '<i class="fas fa-robot"></i>';

    messageDiv.innerHTML = `
        <div class="message-avatar">${icon}</div>
        <div class="message-content">
            ${isTyping ? '<i class="fas fa-spinner fa-spin"></i> ' : ''}${text}
        </div>
    `;

    elements.chatMessages.appendChild(messageDiv);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;

    return messageId;
}

async function clearChat() {
    if (!confirm('¿Limpiar todo el historial de chat?')) return;

    try {
        const response = await fetch('/api/chat/clear', {
            method: 'POST'
        });

        if (response.ok) {
            // Limpiar solo los mensajes del usuario y asistente, mantener el mensaje inicial
            const messages = elements.chatMessages.querySelectorAll('.chat-message');
            messages.forEach((msg, index) => {
                if (index > 0) msg.remove(); // Mantener el primer mensaje de bienvenida
            });
        }
    } catch (error) {
        console.error('Error limpiando chat:', error);
    }
}

// ============================================
// Utilidades
// ============================================

// Manejar errores globales
window.addEventListener('error', (e) => {
    console.error('Error global:', e.error);
});

// Log cuando la página se cierra
window.addEventListener('beforeunload', () => {
    console.log('Cerrando aplicación');
});
