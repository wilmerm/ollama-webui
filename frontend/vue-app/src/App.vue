<template>
  <div class="app-shell">
    <div class="ambient-shape ambient-shape-a"></div>
    <div class="ambient-shape ambient-shape-b"></div>

    <main class="layout">
      <aside class="sidebar">
        <section class="panel card">
          <button class="panel-header" @click="toggleSystemPrompt" type="button">
            <span>Instrucciones del sistema</span>
            <span class="toggle-icon" :class="{ expanded: showSystemPrompt }">⌄</span>
          </button>
          <div class="panel-body" v-show="showSystemPrompt">
            <textarea
              v-model="systemPrompt"
              class="field-textarea"
              :disabled="awaitingResponse"
              placeholder="Define el comportamiento del asistente..."
            ></textarea>
            <div class="inline-actions">
              <button class="ghost" @click="clearSystemPrompt" :disabled="!systemPrompt.trim() || awaitingResponse" type="button">
                Limpiar
              </button>
              <button class="solid" @click="usePresetPrompt" :disabled="awaitingResponse" type="button">
                Ejemplo
              </button>
            </div>
          </div>
        </section>

        <section class="panel card">
          <button class="panel-header" @click="toggleModelSelector" type="button">
            <span>Modelo</span>
            <span class="toggle-icon" :class="{ expanded: showModelSelector }">⌄</span>
          </button>
          <div class="panel-body" v-show="showModelSelector">
            <label for="model-select" class="field-label">Modelo activo</label>
            <select id="model-select" v-model="selectedModel" class="field-select" :disabled="awaitingResponse">
              <option value="" disabled>Seleccionar modelo...</option>
              <option v-for="model in availableModels" :key="model.name" :value="model.name">
                {{ model.name }} ({{ model.size }})
              </option>
            </select>

            <div v-if="selectedModelDetails" class="model-summary">
              <div class="model-row">
                <strong>{{ selectedModelDetails.name }}</strong>
                <span class="status-chip" :class="selectedModelDetails.running ? 'ok' : 'idle'">
                  {{ selectedModelDetails.running ? 'Activo' : 'Inactivo' }}
                </span>
              </div>
              <small>Tamaño: {{ selectedModelDetails.size }} · Modificado: {{ selectedModelDetails.modified }}</small>
            </div>

            <button class="ghost full" @click="refreshModels" :disabled="awaitingResponse || loadingModels" type="button">
              {{ loadingModels ? 'Actualizando...' : 'Actualizar modelos' }}
            </button>
          </div>
        </section>

        <section class="panel card">
          <button class="panel-header" @click="toggleTemperatureControl" type="button">
            <span>Temperatura</span>
            <span class="toggle-icon" :class="{ expanded: showTemperatureControl }">⌄</span>
          </button>
          <div class="panel-body" v-show="showTemperatureControl">
            <label for="temperature-slider" class="field-label">
              {{ temperature.toFixed(1) }} · {{ temperatureProfile }}
            </label>
            <input
              id="temperature-slider"
              class="temperature-slider"
              type="range"
              v-model.number="temperature"
              min="0"
              max="2"
              step="0.1"
              :disabled="awaitingResponse"
            />
            <div class="marks">
              <span>0.0</span>
              <span>1.0</span>
              <span>2.0</span>
            </div>
          </div>
        </section>

        <section class="panel card stream-card">
          <label class="stream-toggle">
            <input type="checkbox" v-model="stream" :disabled="awaitingResponse" />
            <span>Respuesta en streaming</span>
          </label>
        </section>
      </aside>

      <section class="chat card">
        <header class="chat-header">
          <div>
            <h1>Ollama WebUI</h1>
            <p>Chat local con control de modelo y parámetros</p>
          </div>
          <div class="chat-tools">
            <span v-if="selectedModel" class="chip">{{ selectedModel }}</span>
            <button class="ghost" @click="clearConversation" :disabled="awaitingResponse || messages.length === 0" type="button">
              Limpiar chat
            </button>
            <button class="warn" v-if="awaitingResponse" @click="stopGeneration" type="button">
              Detener
            </button>
          </div>
        </header>

        <div class="chat-box" ref="chatBox">
          <article
            v-for="(msg, index) in messages"
            :key="index"
            class="message"
            :class="msg.role === 'assistant' ? 'assistant-message' : 'user-message'"
          >
            <div class="message-meta">
              <span class="avatar">{{ msg.role === 'assistant' ? 'AI' : 'Tu' }}</span>
              <button
                v-if="msg.role === 'assistant'"
                class="ghost mini"
                @click="copyMessage(msg.content)"
                type="button"
              >
                Copiar
              </button>
            </div>
            <div class="message-content" :class="{ typewriter: msg.role === 'assistant' && msg.isTyping }" v-html="msg.formattedContent || msg.content"></div>

            <div v-if="index === messages.length - 1 && awaitingResponse" class="typing-indicator">
              <div class="dot"></div>
              <div class="dot"></div>
              <div class="dot"></div>
            </div>
          </article>

          <div v-if="messages.length === 0" class="empty-state">
            <h2>Empieza una conversación</h2>
            <p>Selecciona un modelo y escribe tu primer prompt.</p>
          </div>
        </div>

        <footer class="composer">
          <textarea
            v-model="prompt"
            placeholder="Escribe tu mensaje. Enter envia, Shift+Enter agrega salto de linea"
            @keydown.enter.exact.prevent="sendPrompt"
            :disabled="awaitingResponse"
          ></textarea>
          <button class="solid send" @click="sendPrompt" :disabled="!canSendPrompt" type="button">
            {{ awaitingResponse ? 'Enviando...' : 'Enviar' }}
          </button>
        </footer>
      </section>
    </main>

    <div class="notifications">
      <div v-for="item in notifications" :key="item.id" class="notification" :class="item.type">
        {{ item.message }}
      </div>
    </div>
  </div>
</template>

<script>
import hljs from 'highlight.js/lib/core';
import css from 'highlight.js/lib/languages/css';
import javascript from 'highlight.js/lib/languages/javascript';
import json from 'highlight.js/lib/languages/json';
import markdown from 'highlight.js/lib/languages/markdown';
import python from 'highlight.js/lib/languages/python';
import html from 'highlight.js/lib/languages/xml';
import MarkdownIt from 'markdown-it';
import { markRaw } from 'vue';
import systemPromptCrypto from './utils/crypto.js';

hljs.registerLanguage('javascript', javascript);
hljs.registerLanguage('python', python);
hljs.registerLanguage('html', html);
hljs.registerLanguage('xml', html);
hljs.registerLanguage('css', css);
hljs.registerLanguage('json', json);
hljs.registerLanguage('markdown', markdown);

export default {
  data() {
    return {
      prompt: '',
      messages: [],
      systemPrompt: '',
      showSystemPrompt: true,
      availableModels: [],
      selectedModel: '',
      showModelSelector: true,
      loadingModels: false,
      temperature: 0.5,
      showTemperatureControl: true,
      stream: true,
      awaitingResponse: false,
      currentStream: null,
      saveTimeout: null,
      notifications: [],
      notificationCounter: 0,
      md: markRaw(
        new MarkdownIt({
          html: false,
          linkify: true,
          typographer: true,
          highlight(str, lang) {
            if (lang && hljs.getLanguage(lang)) {
              try {
                return `<pre class="hljs"><code class="hljs-code">${hljs.highlight(str, { language: lang, ignoreIllegals: true }).value}</code></pre>`;
              } catch (_) {
                // Continue with escaped output.
              }
            }
            return `<pre class="hljs"><code class="hljs-code">${this.utils.escapeHtml(str)}</code></pre>`;
          }
        })
      )
    };
  },

  computed: {
    canSendPrompt() {
      return this.prompt.trim().length > 0 && !this.awaitingResponse;
    },
    selectedModelDetails() {
      return this.availableModels.find((m) => m.name === this.selectedModel) || null;
    },
    temperatureProfile() {
      if (this.temperature <= 0.3) return 'Muy determinista';
      if (this.temperature <= 0.7) return 'Equilibrado';
      if (this.temperature <= 1.2) return 'Creativo';
      return 'Muy creativo';
    }
  },

  async mounted() {
    this.VITE_SERVER_BASE_URL = import.meta.env.VITE_SERVER_BASE_URL || '';
    this.scrollToBottom();
    this.loadUiState();
    await this.loadSystemPrompt();
    this.loadTemperature();
    this.loadStream();
    await this.fetchAvailableModels();
  },

  watch: {
    systemPrompt() {
      this.debounceSaveSystemPrompt();
    },
    selectedModel(newValue) {
      if (newValue) {
        localStorage.setItem('ollama-webui-selected-model', newValue);
      } else {
        localStorage.removeItem('ollama-webui-selected-model');
      }
    },
    temperature(newValue) {
      localStorage.setItem('ollama-webui-temperature', newValue.toString());
    },
    stream(newValue) {
      localStorage.setItem('ollama-webui-stream', newValue.toString());
    },
    showSystemPrompt() {
      this.saveUiState();
    },
    showModelSelector() {
      this.saveUiState();
    },
    showTemperatureControl() {
      this.saveUiState();
    }
  },

  beforeUnmount() {
    if (this.currentStream) {
      this.currentStream.abort();
      this.currentStream = null;
    }
    if (this.saveTimeout) {
      clearTimeout(this.saveTimeout);
      this.saveSystemPrompt();
    }
  },

  methods: {
    async sendPrompt() {
      if (!this.canSendPrompt) return;

      const trimmedPrompt = this.prompt.trim();
      const userMessage = {
        role: 'user',
        content: trimmedPrompt,
        formattedContent: this.md.render(trimmedPrompt)
      };

      this.messages.push(userMessage);
      this.prompt = '';
      this.awaitingResponse = true;

      const aiMessage = {
        role: 'assistant',
        content: '',
        formattedContent: '',
        isTyping: true
      };
      this.messages.push(aiMessage);
      this.smoothScrollToBottom();

      try {
        this.currentStream = new AbortController();
        const response = await fetch(`${this.VITE_SERVER_BASE_URL}/api/ollama`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          signal: this.currentStream.signal,
          body: JSON.stringify({
            messages: this.buildMessagesToSend(),
            model: this.selectedModel || undefined,
            temperature: this.temperature,
            stream: this.stream
          })
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`Error ${response.status}: ${errorText}`);
        }

        if (this.stream) {
          await this.consumeStreamResponse(response, aiMessage);
        } else {
          const data = await response.json();
          const content = data?.response || data?.message?.content;
          if (!content) {
            throw new Error('Respuesta no valida del servidor');
          }
          aiMessage.content = content;
          aiMessage.formattedContent = this.md.render(this.preprocessThinkingTags(content));
          this.messages = [...this.messages];
        }

        aiMessage.isTyping = false;
        this.smoothScrollToBottom();
      } catch (error) {
        let errorMessage = 'Error de conexion con el servidor';
        if (error.name === 'AbortError') {
          errorMessage = 'Generacion detenida por el usuario';
        } else if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
          errorMessage = 'No se puede conectar con el servidor. Verifica que este ejecutandose.';
        } else if (error.message) {
          errorMessage = 'Error procesando la solicitud. Intentalo de nuevo.';
        }

        aiMessage.content = `❌ ${errorMessage}`;
        aiMessage.formattedContent = this.md.render(aiMessage.content);
        aiMessage.isTyping = false;
        this.messages = [...this.messages];
        this.showNotification(errorMessage, 'error');
      } finally {
        this.currentStream = null;
        this.awaitingResponse = false;
        this.smoothScrollToBottom();
      }
    },

    buildMessagesToSend() {
      const payload = [];
      if (this.systemPrompt.trim()) {
        payload.push({ role: 'system', content: this.systemPrompt.trim() });
      }
      payload.push(...this.messages.slice(0, -1).map((msg) => ({ role: msg.role, content: msg.content })));
      return payload;
    },

    async consumeStreamResponse(response, aiMessage) {
      if (!response.body) {
        throw new Error('El servidor no devolvio un stream valido');
      }

      const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        if (!value) continue;

        buffer += value;
        let lineBreakIndex;
        while ((lineBreakIndex = buffer.indexOf('\n')) >= 0) {
          const rawLine = buffer.slice(0, lineBreakIndex);
          buffer = buffer.slice(lineBreakIndex + 1);
          this.processOllamaChunk(rawLine, aiMessage);
        }
      }

      if (buffer.trim()) {
        this.processOllamaChunk(buffer, aiMessage);
      }
    },

    processOllamaChunk(rawLine, aiMessage) {
      if (!rawLine) return;

      const line = rawLine.trim();
      if (!line) return;

      const normalizedLine = line.startsWith('data:') ? line.slice(5).trim() : line;
      if (!normalizedLine || normalizedLine === '[DONE]') return;

      try {
        const chunk = JSON.parse(normalizedLine);
        if (chunk.error) {
          throw new Error(chunk.error);
        }

        const contentChunk = chunk?.message?.content || chunk?.response || '';
        if (!contentChunk) return;

        aiMessage.content += contentChunk;
        aiMessage.formattedContent = this.md.render(this.preprocessThinkingTags(aiMessage.content));
        this.messages = [...this.messages];
      } catch (error) {
        console.error('Error parsing stream chunk:', normalizedLine, error);
      }
    },

    preprocessThinkingTags(content) {
      if (!content || typeof content !== 'string') {
        return content;
      }

      const asQuoteBlock = (text) =>
        text
          .trim()
          .split('\n')
          .map((line) => `> ${line}`)
          .join('\n');

      let processed = content.replace(/<think>([\s\S]*?)<\/think>/gi, (_, thought) => {
        const quoted = asQuoteBlock(thought);
        return `\n> 💭 Pensamiento interno\n${quoted}\n`;
      });

      processed = processed.replace(/<thinking>([\s\S]*?)<\/thinking>/gi, (_, thought) => {
        const quoted = asQuoteBlock(thought);
        return `\n> 💭 Pensamiento interno\n${quoted}\n`;
      });

      return processed;
    },

    stopGeneration() {
      if (!this.currentStream) return;
      this.currentStream.abort();
    },

    clearConversation() {
      this.messages = [];
      this.showNotification('Chat limpiado', 'success');
    },

    async copyMessage(content) {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        try {
          await navigator.clipboard.writeText(content);
          this.showNotification('Mensaje copiado al portapapeles', 'success');
          return;
        } catch (_) {
          // Try fallback below.
        }
      }
      this.copyMessageFallback(content);
    },

    copyMessageFallback(content) {
      try {
        const textArea = document.createElement('textarea');
        textArea.value = content;
        textArea.style.position = 'fixed';
        textArea.style.left = '-9999px';
        textArea.style.opacity = '0';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        const successful = document.execCommand('copy');
        document.body.removeChild(textArea);

        if (!successful) {
          throw new Error('No se pudo copiar');
        }

        this.showNotification('Mensaje copiado al portapapeles', 'success');
      } catch (_) {
        this.showNotification('No se pudo copiar el mensaje', 'error');
      }
    },

    toggleSystemPrompt() {
      this.showSystemPrompt = !this.showSystemPrompt;
    },
    toggleModelSelector() {
      this.showModelSelector = !this.showModelSelector;
    },
    toggleTemperatureControl() {
      this.showTemperatureControl = !this.showTemperatureControl;
    },

    clearSystemPrompt() {
      this.systemPrompt = '';
      this.saveSystemPrompt();
    },

    usePresetPrompt() {
      this.systemPrompt = 'Eres un asistente util que responde de forma clara, breve y accionable.';
      this.saveSystemPrompt();
    },

    async loadSystemPrompt() {
      try {
        if (systemPromptCrypto.constructor.isSupported()) {
          const savedPrompt = await systemPromptCrypto.loadSystemPrompt();
          if (savedPrompt) {
            this.systemPrompt = savedPrompt;
          }
        } else {
          const fallbackPrompt = localStorage.getItem('ollama-webui-system-prompt-unencrypted');
          if (fallbackPrompt) {
            this.systemPrompt = fallbackPrompt;
          }
        }
      } catch (_) {
        this.showNotification('No se pudo recuperar el prompt del sistema', 'error');
      }
    },

    async saveSystemPrompt() {
      try {
        if (systemPromptCrypto.constructor.isSupported()) {
          await systemPromptCrypto.saveSystemPrompt(this.systemPrompt);
          return;
        }
        if (!this.systemPrompt || this.systemPrompt.trim() === '') {
          localStorage.removeItem('ollama-webui-system-prompt-unencrypted');
        } else {
          localStorage.setItem('ollama-webui-system-prompt-unencrypted', this.systemPrompt);
        }
      } catch (_) {
        this.showNotification('No se pudo guardar el prompt del sistema', 'error');
      }
    },

    debounceSaveSystemPrompt() {
      if (this.saveTimeout) {
        clearTimeout(this.saveTimeout);
      }
      this.saveTimeout = setTimeout(() => {
        this.saveSystemPrompt();
      }, 600);
    },

    showNotification(message, type = 'success') {
      const id = ++this.notificationCounter;
      this.notifications.push({ id, message, type });
      window.setTimeout(() => {
        this.notifications = this.notifications.filter((item) => item.id !== id);
      }, type === 'error' ? 4200 : 2600);
    },

    smoothScrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.chatBox;
        if (!container) return;
        container.scrollTo({
          top: container.scrollHeight,
          behavior: 'smooth'
        });
      });
    },

    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.chatBox;
        if (!container) return;
        container.scrollTop = container.scrollHeight;
      });
    },

    saveUiState() {
      localStorage.setItem(
        'ollama-webui-ui-state',
        JSON.stringify({
          showSystemPrompt: this.showSystemPrompt,
          showModelSelector: this.showModelSelector,
          showTemperatureControl: this.showTemperatureControl
        })
      );
    },

    loadUiState() {
      try {
        const saved = localStorage.getItem('ollama-webui-ui-state');
        if (!saved) return;
        const parsed = JSON.parse(saved);
        this.showSystemPrompt = parsed.showSystemPrompt ?? this.showSystemPrompt;
        this.showModelSelector = parsed.showModelSelector ?? this.showModelSelector;
        this.showTemperatureControl = parsed.showTemperatureControl ?? this.showTemperatureControl;
      } catch (_) {
        // Ignore invalid local storage data.
      }
    },

    async fetchAvailableModels() {
      this.loadingModels = true;
      try {
        const response = await fetch(`${this.VITE_SERVER_BASE_URL}/api/models`);
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        this.availableModels = data.models || [];

        const savedModel = localStorage.getItem('ollama-webui-selected-model');
        if (savedModel && this.availableModels.some((m) => m.name === savedModel)) {
          this.selectedModel = savedModel;
        } else if (this.availableModels.length > 0) {
          const runningModel = this.availableModels.find((m) => m.running);
          this.selectedModel = runningModel ? runningModel.name : this.availableModels[0].name;
        }
      } catch (_) {
        this.showNotification('No se pudieron cargar los modelos', 'error');
      } finally {
        this.loadingModels = false;
      }
    },

    async refreshModels() {
      await this.fetchAvailableModels();
      this.showNotification('Modelos actualizados', 'success');
    },

    loadTemperature() {
      const savedTemperature = localStorage.getItem('ollama-webui-temperature');
      if (!savedTemperature) return;
      const value = Number.parseFloat(savedTemperature);
      if (!Number.isNaN(value) && value >= 0 && value <= 2) {
        this.temperature = value;
      }
    },

    loadStream() {
      const savedStream = localStorage.getItem('ollama-webui-stream');
      if (!savedStream) return;
      this.stream = savedStream === 'true';
    }
  }
};
</script>

<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700;800&family=IBM+Plex+Mono:wght@400;500&display=swap');
@import 'highlight.js/styles/github-dark.css';

:root {
  --bg: #f6f4ef;
  --bg-soft: #efe8dc;
  --surface: #fffdf8;
  --surface-2: #f9f4ea;
  --text: #262322;
  --muted: #665f57;
  --line: #dccfbc;
  --primary: #0b7a75;
  --primary-strong: #075c58;
  --accent: #e17a28;
  --danger: #c63f2f;
  --success: #2f8f55;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: 'Manrope', sans-serif;
  color: var(--text);
  background: radial-gradient(circle at 12% 18%, #f8ebcf 0%, transparent 42%),
    radial-gradient(circle at 85% 10%, #d9efe8 0%, transparent 32%),
    linear-gradient(180deg, #faf7f1 0%, #f0ebe2 100%);
}

#app {
  min-height: 100vh;
}

.app-shell {
  min-height: 100vh;
  padding: 1rem;
  position: relative;
  isolation: isolate;
}

.ambient-shape {
  position: absolute;
  border-radius: 999px;
  filter: blur(32px);
  z-index: -1;
  opacity: 0.45;
}

.ambient-shape-a {
  width: 280px;
  height: 280px;
  top: -60px;
  left: -40px;
  background: #f8d6a9;
}

.ambient-shape-b {
  width: 320px;
  height: 320px;
  right: -60px;
  bottom: 8%;
  background: #bde6da;
}

.layout {
  max-width: 1280px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 330px 1fr;
  gap: 1rem;
  align-items: start;
}

.card {
  border: 1px solid var(--line);
  background: color-mix(in srgb, var(--surface), white 16%);
  box-shadow: 0 12px 34px rgba(28, 31, 35, 0.08);
  border-radius: 18px;
}

.sidebar {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  position: sticky;
  top: 1rem;
}

.panel {
  overflow: clip;
}

.panel-header {
  width: 100%;
  border: 0;
  background: var(--surface-2);
  border-bottom: 1px solid var(--line);
  color: var(--text);
  font-family: inherit;
  font-weight: 700;
  letter-spacing: 0.01em;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.85rem 1rem;
  cursor: pointer;
}

.toggle-icon {
  transition: transform 0.18s ease;
}

.toggle-icon.expanded {
  transform: rotate(180deg);
}

.panel-body {
  padding: 0.85rem 1rem 1rem;
}

.field-label {
  display: block;
  margin-bottom: 0.4rem;
  color: var(--muted);
  font-size: 0.9rem;
}

.field-textarea,
.field-select,
.composer textarea {
  width: 100%;
  border: 1px solid var(--line);
  background: white;
  color: var(--text);
  border-radius: 12px;
  padding: 0.75rem 0.85rem;
  font-family: inherit;
  resize: vertical;
}

.field-textarea:focus,
.field-select:focus,
.composer textarea:focus {
  outline: 2px solid color-mix(in srgb, var(--primary), white 70%);
  border-color: color-mix(in srgb, var(--primary), white 35%);
}

.field-textarea {
  min-height: 94px;
}

.inline-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  margin-top: 0.65rem;
}

button {
  border: 0;
  border-radius: 12px;
  cursor: pointer;
  font-family: inherit;
  font-weight: 700;
  transition: transform 0.16s ease, opacity 0.16s ease, background-color 0.16s ease;
}

button:hover:not(:disabled) {
  transform: translateY(-1px);
}

button:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.solid {
  background: var(--primary);
  color: #ffffff;
  padding: 0.6rem 0.85rem;
}

.solid:hover:not(:disabled) {
  background: var(--primary-strong);
}

.ghost {
  background: #fff;
  color: var(--text);
  border: 1px solid var(--line);
  padding: 0.58rem 0.85rem;
}

.warn {
  background: var(--danger);
  color: #fff;
  padding: 0.58rem 0.85rem;
}

.full {
  width: 100%;
  margin-top: 0.7rem;
}

.marks {
  margin-top: 0.45rem;
  display: flex;
  justify-content: space-between;
  color: var(--muted);
  font-size: 0.83rem;
}

.temperature-slider {
  width: 100%;
  accent-color: var(--accent);
}

.stream-card {
  padding: 0.6rem 1rem;
}

.stream-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  color: var(--muted);
  font-weight: 600;
}

.model-summary {
  margin-top: 0.75rem;
  border: 1px dashed var(--line);
  border-radius: 10px;
  padding: 0.65rem;
  background: #fff;
}

.model-row {
  display: flex;
  justify-content: space-between;
  gap: 0.5rem;
  align-items: center;
}

.status-chip {
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.2rem 0.65rem;
}

.status-chip.ok {
  background: color-mix(in srgb, var(--success), white 80%);
  color: #23653d;
}

.status-chip.idle {
  background: #ece8e3;
  color: #7f7568;
}

.chat {
  min-height: calc(100vh - 2rem);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-header {
  display: flex;
  justify-content: space-between;
  gap: 0.8rem;
  align-items: flex-start;
  padding: 1rem 1.1rem;
  border-bottom: 1px solid var(--line);
  background: linear-gradient(90deg, rgba(230, 247, 242, 0.8), rgba(252, 241, 223, 0.8));
}

.chat-header h1 {
  font-size: clamp(1.1rem, 2vw, 1.45rem);
  margin: 0;
}

.chat-header p {
  margin: 0.2rem 0 0;
  color: var(--muted);
  font-size: 0.9rem;
}

.chat-tools {
  display: flex;
  gap: 0.45rem;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.chip {
  background: color-mix(in srgb, var(--primary), white 84%);
  color: var(--primary-strong);
  border-radius: 999px;
  padding: 0.34rem 0.74rem;
  font-size: 0.76rem;
  font-weight: 700;
  align-self: center;
}

.chat-box {
  flex: 1;
  overflow-y: auto;
  padding: 1.1rem;
  scroll-behavior: smooth;
}

.message {
  border-radius: 14px;
  margin-bottom: 0.85rem;
  padding: 0.9rem;
  border: 1px solid transparent;
}

.user-message {
  margin-left: 2.5rem;
  background: #fff;
  border-color: #e4d6c4;
}

.assistant-message {
  margin-right: 2.5rem;
  background: #f9fffc;
  border-color: #cae9de;
}

.message-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.55rem;
}

.avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2rem;
  height: 2rem;
  border-radius: 999px;
  background: var(--surface-2);
  border: 1px solid var(--line);
  font-size: 0.77rem;
  font-weight: 800;
  letter-spacing: 0.03em;
}

.mini {
  font-size: 0.78rem;
  padding: 0.34rem 0.6rem;
}

.message-content {
  line-height: 1.6;
  font-size: 0.98rem;
}

.typewriter {
  border-right: 2px solid color-mix(in srgb, var(--primary), white 50%);
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  from,
  to {
    border-color: transparent;
  }
  50% {
    border-color: color-mix(in srgb, var(--primary), white 50%);
  }
}

.typing-indicator {
  display: flex;
  gap: 0.28rem;
  margin-top: 0.45rem;
}

.dot {
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: var(--accent);
  animation: pulse 1.2s infinite ease-in-out;
}

.dot:nth-child(2) {
  animation-delay: 0.15s;
}

.dot:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes pulse {
  0%,
  80%,
  100% {
    transform: translateY(0);
    opacity: 0.55;
  }
  40% {
    transform: translateY(-3px);
    opacity: 1;
  }
}

.empty-state {
  border: 1px dashed var(--line);
  border-radius: 14px;
  padding: 1.4rem;
  text-align: center;
  color: var(--muted);
  background: #fff;
}

.empty-state h2 {
  margin: 0 0 0.3rem;
  font-size: 1.1rem;
  color: var(--text);
}

.composer {
  border-top: 1px solid var(--line);
  padding: 0.85rem;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 0.55rem;
  align-items: end;
}

.composer textarea {
  min-height: 74px;
  max-height: 220px;
}

.send {
  height: fit-content;
  padding: 0.72rem 1rem;
}

.message-content pre {
  border-radius: 10px;
  overflow-x: auto;
  border: 1px solid #394049;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.04);
}

.message-content code {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.9em;
}

.message-content :not(pre) > code {
  background: color-mix(in srgb, var(--surface-2), white 15%);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 0.1rem 0.34rem;
}

.message-content blockquote {
  margin: 0.8rem 0;
  border-left: 3px solid var(--accent);
  padding: 0.5rem 0.8rem;
  color: #5b524a;
  background: rgba(225, 122, 40, 0.08);
}

.notifications {
  position: fixed;
  top: 1rem;
  right: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  z-index: 40;
}

.notification {
  border-radius: 10px;
  padding: 0.6rem 0.8rem;
  color: white;
  font-weight: 700;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
}

.notification.success {
  background: var(--success);
}

.notification.error {
  background: var(--danger);
}

@media (max-width: 1024px) {
  .layout {
    grid-template-columns: 1fr;
  }

  .sidebar {
    position: static;
    top: auto;
  }

  .chat {
    min-height: 70vh;
  }
}

@media (max-width: 720px) {
  .app-shell {
    padding: 0.65rem;
  }

  .chat-header {
    flex-direction: column;
  }

  .user-message,
  .assistant-message {
    margin-inline: 0;
  }

  .composer {
    grid-template-columns: 1fr;
  }

  .send {
    width: 100%;
  }

  .notifications {
    left: 0.65rem;
    right: 0.65rem;
    top: 0.65rem;
  }
}
</style>
