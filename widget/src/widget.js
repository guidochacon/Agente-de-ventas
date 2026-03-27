/**
 * SalesAgentWidget — self-contained embeddable chat widget.
 * Reads config from window.SalesAgentConfig.
 */

(function () {
  const DEFAULT_CONFIG = {
    agentUrl: '',
    agentName: 'Alex',
    primaryColor: '#2563EB',
    welcomeMessage: '¡Hola! ¿En qué puedo ayudarte hoy?',
    companyLogo: '',
    collectLeadAfterMessages: 2,
    position: 'bottom-right',
  };

  const config = Object.assign({}, DEFAULT_CONFIG, window.SalesAgentConfig || {});

  // Derive WebSocket URL from agentUrl
  function getWsUrl(sessionId) {
    const base = config.agentUrl.replace(/\/$/, '');
    const wsBase = base.replace(/^http/, 'ws');
    return `${wsBase}/api/chat/${sessionId}`;
  }

  function generateSessionId() {
    const stored = sessionStorage.getItem('sa_session_id');
    if (stored) return stored;
    const id = 'sa-' + Math.random().toString(36).slice(2, 11);
    sessionStorage.setItem('sa_session_id', id);
    return id;
  }

  // ── Styles ────────────────────────────────────────────────────────────────
  function injectStyles() {
    const css = `
      #sa-widget-container * { box-sizing: border-box; font-family: system-ui, -apple-system, sans-serif; }
      #sa-bubble {
        position: fixed; ${config.position === 'bottom-left' ? 'left: 24px;' : 'right: 24px;'} bottom: 24px;
        width: 56px; height: 56px; border-radius: 50%;
        background: ${config.primaryColor}; color: white; font-size: 24px;
        display: flex; align-items: center; justify-content: center;
        cursor: pointer; box-shadow: 0 4px 20px rgba(0,0,0,0.25);
        z-index: 9998; border: none; transition: transform 0.2s;
        user-select: none;
      }
      #sa-bubble:hover { transform: scale(1.08); }
      #sa-panel {
        position: fixed; ${config.position === 'bottom-left' ? 'left: 24px;' : 'right: 24px;'} bottom: 88px;
        width: 360px; max-width: calc(100vw - 48px);
        height: 520px; max-height: calc(100vh - 120px);
        background: #fff; border-radius: 16px;
        box-shadow: 0 8px 40px rgba(0,0,0,0.18);
        display: flex; flex-direction: column;
        z-index: 9999; overflow: hidden;
        transform: scale(0.95) translateY(8px); opacity: 0;
        transition: transform 0.2s, opacity 0.2s;
        pointer-events: none;
      }
      #sa-panel.sa-open { transform: scale(1) translateY(0); opacity: 1; pointer-events: all; }
      #sa-header {
        background: ${config.primaryColor}; color: white;
        padding: 14px 16px; display: flex; align-items: center; gap: 10px;
        flex-shrink: 0;
      }
      #sa-header-avatar {
        width: 36px; height: 36px; border-radius: 50%; background: rgba(255,255,255,0.25);
        display: flex; align-items: center; justify-content: center; font-size: 16px; flex-shrink: 0;
      }
      #sa-header-info { flex: 1; }
      #sa-header-name { font-weight: 700; font-size: 15px; }
      #sa-header-status { font-size: 12px; opacity: 0.8; }
      #sa-close-btn { background: none; border: none; color: white; font-size: 20px; cursor: pointer; padding: 0; opacity: 0.8; line-height: 1; }
      #sa-close-btn:hover { opacity: 1; }
      #sa-messages {
        flex: 1; overflow-y: auto; padding: 16px; display: flex;
        flex-direction: column; gap: 10px;
        scroll-behavior: smooth;
      }
      .sa-message {
        max-width: 82%; padding: 10px 14px; border-radius: 14px;
        font-size: 14px; line-height: 1.5; word-wrap: break-word;
        animation: sa-fadeIn 0.15s ease;
      }
      @keyframes sa-fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
      .sa-message.sa-user {
        align-self: flex-end; background: ${config.primaryColor}; color: white;
        border-bottom-right-radius: 4px;
      }
      .sa-message.sa-agent {
        align-self: flex-start; background: #f1f5f9; color: #1a1a1a;
        border-bottom-left-radius: 4px;
      }
      .sa-typing { display: flex; gap: 4px; align-items: center; padding: 12px 16px; }
      .sa-typing span {
        width: 7px; height: 7px; border-radius: 50%; background: #94a3b8;
        animation: sa-bounce 1.2s infinite;
      }
      .sa-typing span:nth-child(2) { animation-delay: 0.2s; }
      .sa-typing span:nth-child(3) { animation-delay: 0.4s; }
      @keyframes sa-bounce { 0%,60%,100% { transform: translateY(0); } 30% { transform: translateY(-6px); } }
      #sa-input-area {
        display: flex; gap: 8px; padding: 12px 14px;
        border-top: 1px solid #e5e7eb; flex-shrink: 0;
      }
      #sa-input {
        flex: 1; border: 1.5px solid #e2e8f0; border-radius: 24px;
        padding: 9px 16px; font-size: 14px; outline: none; resize: none;
        max-height: 100px; overflow-y: auto;
        transition: border-color 0.15s;
      }
      #sa-input:focus { border-color: ${config.primaryColor}; }
      #sa-send-btn {
        width: 38px; height: 38px; border-radius: 50%;
        background: ${config.primaryColor}; color: white; border: none;
        cursor: pointer; display: flex; align-items: center; justify-content: center;
        font-size: 16px; transition: background 0.15s; flex-shrink: 0;
      }
      #sa-send-btn:hover { filter: brightness(1.1); }
      #sa-send-btn:disabled { opacity: 0.5; cursor: not-allowed; }
    `;
    const style = document.createElement('style');
    style.textContent = css;
    document.head.appendChild(style);
  }

  // ── DOM ───────────────────────────────────────────────────────────────────
  function buildDOM() {
    const container = document.createElement('div');
    container.id = 'sa-widget-container';

    container.innerHTML = `
      <button id="sa-bubble" title="Chat con ${config.agentName}">💬</button>
      <div id="sa-panel" role="dialog" aria-label="Chat de ventas">
        <div id="sa-header">
          <div id="sa-header-avatar">🤖</div>
          <div id="sa-header-info">
            <div id="sa-header-name">${config.agentName}</div>
            <div id="sa-header-status">Conectando...</div>
          </div>
          <button id="sa-close-btn" aria-label="Cerrar chat">✕</button>
        </div>
        <div id="sa-messages"></div>
        <div id="sa-input-area">
          <textarea id="sa-input" rows="1" placeholder="Escribí tu mensaje..." aria-label="Mensaje"></textarea>
          <button id="sa-send-btn" aria-label="Enviar">➤</button>
        </div>
      </div>
    `;

    document.body.appendChild(container);
    return container;
  }

  // ── Widget Class ─────────────────────────────────────────────────────────
  function SalesAgentWidget() {
    this.sessionId = generateSessionId();
    this.ws = null;
    this.isOpen = false;
    this.isTyping = false;
    this.currentAssistantMsg = null;
    this.messageCount = 0;

    injectStyles();
    buildDOM();

    this.bubble = document.getElementById('sa-bubble');
    this.panel = document.getElementById('sa-panel');
    this.messages = document.getElementById('sa-messages');
    this.input = document.getElementById('sa-input');
    this.sendBtn = document.getElementById('sa-send-btn');
    this.statusEl = document.getElementById('sa-header-status');

    this._bindEvents();
    this._connect();
  }

  SalesAgentWidget.prototype._bindEvents = function () {
    const self = this;

    this.bubble.addEventListener('click', function () {
      self.toggle();
    });

    document.getElementById('sa-close-btn').addEventListener('click', function () {
      self.close();
    });

    this.sendBtn.addEventListener('click', function () {
      self._sendMessage();
    });

    this.input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        self._sendMessage();
      }
    });

    // Auto-resize textarea
    this.input.addEventListener('input', function () {
      this.style.height = 'auto';
      this.style.height = Math.min(this.scrollHeight, 100) + 'px';
    });
  };

  SalesAgentWidget.prototype._connect = function () {
    const self = this;
    const wsUrl = getWsUrl(this.sessionId);

    try {
      this.ws = new WebSocket(wsUrl);
    } catch (e) {
      this._setStatus('Error de conexión');
      return;
    }

    this.ws.onopen = function () {
      self._setStatus('En línea');
      // Show welcome message
      self._addAgentMessage(config.welcomeMessage);
    };

    this.ws.onclose = function () {
      self._setStatus('Desconectado');
      // Reconnect after 3s
      setTimeout(function () { self._connect(); }, 3000);
    };

    this.ws.onerror = function () {
      self._setStatus('Error de conexión');
    };

    this.ws.onmessage = function (event) {
      try {
        const data = JSON.parse(event.data);
        self._handleMessage(data);
      } catch (e) {}
    };
  };

  SalesAgentWidget.prototype._handleMessage = function (data) {
    if (data.type === 'start') {
      this._removeTyping();
      this.currentAssistantMsg = this._addAgentMessage('');
      this.sendBtn.disabled = true;
    } else if (data.type === 'token') {
      if (this.currentAssistantMsg) {
        this.currentAssistantMsg.textContent += data.text;
        this._scrollToBottom();
      }
    } else if (data.type === 'tool_call') {
      // Show subtle indicator
      if (this.currentAssistantMsg) {
        this.currentAssistantMsg.textContent += ' ';
      }
    } else if (data.type === 'end') {
      this.currentAssistantMsg = null;
      this.sendBtn.disabled = false;
      this.messageCount++;
      this._scrollToBottom();
    } else if (data.type === 'error') {
      this._removeTyping();
      this._addAgentMessage('Lo siento, hubo un error. Intentá de nuevo.');
      this.sendBtn.disabled = false;
    }
  };

  SalesAgentWidget.prototype._sendMessage = function () {
    const text = this.input.value.trim();
    if (!text) return;
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      this._addAgentMessage('Estoy reconectando, intentá en un momento...');
      return;
    }

    this._addUserMessage(text);
    this.input.value = '';
    this.input.style.height = 'auto';
    this.sendBtn.disabled = true;
    this._addTyping();

    this.ws.send(JSON.stringify({ message: text }));
  };

  SalesAgentWidget.prototype._addUserMessage = function (text) {
    const div = document.createElement('div');
    div.className = 'sa-message sa-user';
    div.textContent = text;
    this.messages.appendChild(div);
    this._scrollToBottom();
    return div;
  };

  SalesAgentWidget.prototype._addAgentMessage = function (text) {
    this._removeTyping();
    const div = document.createElement('div');
    div.className = 'sa-message sa-agent';
    div.textContent = text;
    this.messages.appendChild(div);
    this._scrollToBottom();
    return div;
  };

  SalesAgentWidget.prototype._addTyping = function () {
    this._removeTyping();
    const div = document.createElement('div');
    div.className = 'sa-message sa-agent sa-typing';
    div.id = 'sa-typing-indicator';
    div.innerHTML = '<span></span><span></span><span></span>';
    this.messages.appendChild(div);
    this._scrollToBottom();
  };

  SalesAgentWidget.prototype._removeTyping = function () {
    const t = document.getElementById('sa-typing-indicator');
    if (t) t.remove();
  };

  SalesAgentWidget.prototype._scrollToBottom = function () {
    this.messages.scrollTop = this.messages.scrollHeight;
  };

  SalesAgentWidget.prototype._setStatus = function (text) {
    if (this.statusEl) this.statusEl.textContent = text;
  };

  SalesAgentWidget.prototype.toggle = function () {
    this.isOpen ? this.close() : this.open();
  };

  SalesAgentWidget.prototype.open = function () {
    this.isOpen = true;
    this.panel.classList.add('sa-open');
    this.bubble.innerHTML = '✕';
    this.input.focus();
  };

  SalesAgentWidget.prototype.close = function () {
    this.isOpen = false;
    this.panel.classList.remove('sa-open');
    this.bubble.innerHTML = '💬';
  };

  // ── Init ──────────────────────────────────────────────────────────────────
  function init() {
    if (!config.agentUrl) {
      console.warn('[SalesAgent] agentUrl is required in window.SalesAgentConfig');
      return;
    }
    window._salesAgent = new SalesAgentWidget();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
