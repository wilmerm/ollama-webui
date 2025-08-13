<template>
  <div class="container">
    <div class="chat">
      <div class="chat-box" ref="chatBox">
        <div
          v-for="(msg, index) in messages"
          :key="index"
          class="message"
          :class="{ 'assistant-message': msg.role === 'assistant', 'user-message': msg.role === 'user' }"
        >
          <div class="message-header" v-if="msg.role === 'assistant'">
            <span class="message-role">🤖 Asistente</span>
            <button
              class="copy-button"
              @click="copyMessage(msg.content)"
              title="Copiar mensaje"
            >
              📋
            </button>
          </div>
          <div class="message-header" v-else>
            <span class="message-role">👤 Tú</span>
          </div>
          <div
            class="message-content"
            :class="{ 'typewriter': msg.role === 'assistant' && msg.isTyping }"
            v-html="msg.formattedContent || msg.content"
          ></div>
          <div v-if="index === messages.length - 1 && awaitingResponse" class="typing-indicator">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
          </div>
        </div>
      </div>

      <!-- System Prompt Section -->
      <div class="system-prompt-section">
        <div class="system-prompt-header" @click="toggleSystemPrompt">
          <span class="system-prompt-title">⚙️ Instrucciones del Sistema</span>
          <span class="toggle-icon" :class="{ 'expanded': showSystemPrompt }">▼</span>
        </div>
        <div class="system-prompt-container" v-show="showSystemPrompt">
          <textarea
            v-model="systemPrompt"
            placeholder="Eres un asistente útil. Define aquí el comportamiento del modelo..."
            class="system-prompt-input"
            :disabled="awaitingResponse"
          ></textarea>
          <div class="system-prompt-actions">
            <button 
              @click="clearSystemPrompt" 
              class="clear-button"
              :disabled="!systemPrompt.trim() || awaitingResponse"
            >
              🗑️ Limpiar
            </button>
            <button 
              @click="usePresetPrompt" 
              class="preset-button"
              :disabled="awaitingResponse"
            >
              📋 Usar Ejemplo
            </button>
          </div>
        </div>
      </div>

      <div class="input-group">
        <textarea
          v-model="prompt"
          placeholder="Escribe tu mensaje..."
          @keydown.enter.exact.prevent="sendPrompt"
          :disabled="awaitingResponse"
        ></textarea>
        <button @click="sendPrompt" :disabled="awaitingResponse">
          {{ awaitingResponse ? 'Enviando...' : 'Enviar' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { markRaw } from 'vue';
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js/lib/core';
import javascript from 'highlight.js/lib/languages/javascript';
import python from 'highlight.js/lib/languages/python';
import html from 'highlight.js/lib/languages/xml';
import css from 'highlight.js/lib/languages/css';
import json from 'highlight.js/lib/languages/json';
import markdown from 'highlight.js/lib/languages/markdown';
import systemPromptCrypto from './utils/crypto.js';

// Register languages with highlight.js
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
      showSystemPrompt: false,
      md: markRaw(new MarkdownIt({
        html: true,
        linkify: true,
        typographer: true,
        highlight: function (str, lang) {
          if (lang && hljs.getLanguage(lang)) {
            try {
              return '<pre class="hljs"><code class="hljs-code">' +
                     hljs.highlight(str, { language: lang, ignoreIllegals: true }).value +
                     '</code></pre>';
            } catch (__) {}
          }
          return '<pre class="hljs"><code class="hljs-code">' + this.utils.escapeHtml(str) + '</code></pre>';
        }
      })),
      awaitingResponse: false,
      currentStream: null,
      saveTimeout: null, // For debounced saving
    }
  },

  async mounted() {
    this.VITE_SERVER_BASE_URL = import.meta.env.VITE_SERVER_BASE_URL || '';
    this.scrollToBottom();
    await this.loadSystemPrompt();
  },

  watch: {
    systemPrompt(newValue) {
      // Debounced save to avoid too frequent localStorage writes
      this.debounceSaveSystemPrompt();
    }
  },

  beforeUnmount() {
    if (this.saveTimeout) {
      clearTimeout(this.saveTimeout);
    }
  },

  methods: {
    async sendPrompt() {
      if (!this.prompt.trim() || this.awaitingResponse) return;

      const userMessage = {
        role: 'user',
        content: this.prompt.trim(),
        formattedContent: this.md.render(this.prompt.trim())
      };

      this.messages.push(userMessage);
      this.prompt = '';
      this.awaitingResponse = true;

      // Crear mensaje vacío del asistente
      const aiMessage = {
        role: 'assistant',
        content: '',
        formattedContent: '',
        isTyping: true,
      };
      this.messages.push(aiMessage);

      // Prepare messages for API call
      const messagesToSend = [];
      
      // Add system message if present
      if (this.systemPrompt.trim()) {
        messagesToSend.push({
          role: 'system',
          content: this.systemPrompt.trim()
        });
      }
      
      // Add conversation history (excluding the empty assistant message we just added)
      messagesToSend.push(...this.messages
        .slice(0, -1)
        .map(msg => ({ role: msg.role, content: msg.content })));

      try {
        const response = await fetch(`${this.VITE_SERVER_BASE_URL}/api/ollama`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            messages: messagesToSend,
            stream: true
          })
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(`Error ${response.status}: ${errorText}`);
        }

        const reader = response.body
          .pipeThrough(new TextDecoderStream())
          .pipeThrough(this.createLineTransformer())
          .getReader();

        let buffer = '';
        let done = false;

        while (!done) {
          const { value, done: streamDone } = await reader.read();
          done = streamDone;

          if (value) {
            buffer += value;

            // Procesar todos los JSON completos en el buffer
            let lineBreakIndex;

            while ((lineBreakIndex = buffer.indexOf('\n')) >= 0) {
              const line = buffer.slice(0, lineBreakIndex).trim();
              buffer = buffer.slice(lineBreakIndex + 1);

              if (line) {
                try {
                  const chunk = JSON.parse(line);
                  if (chunk.message?.content) {
                    aiMessage.content += chunk.message.content;
                    aiMessage.formattedContent = this.md.render(aiMessage.content);
                    this.messages = [...this.messages];
                    this.smoothScrollToBottom();
                  }
                } catch (error) {
                  console.error('Error parsing JSON chunk:', line, error);
                }
              }
            }
          }
        }

        // Procesar cualquier dato restante en el buffer
        if (buffer.trim()) {
          try {
            const chunk = JSON.parse(buffer.trim());
            if (chunk.message?.content) {
              aiMessage.content += chunk.message.content;
              aiMessage.formattedContent = this.md.render(aiMessage.content);
              this.messages = [...this.messages];
            }
          } catch (error) {
            console.error('Error parsing final chunk:', buffer, error);
          }
        }

        // Finalizar animación de escritura
        aiMessage.isTyping = false;

      } catch (error) {
        console.error('Error:', error);
        let errorMessage = 'Error de conexión con el servidor';

        if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
          errorMessage = 'No se puede conectar con el servidor. Verifica que esté ejecutándose.';
        } else if (error.message) {
          // Don't expose detailed error messages from server
          errorMessage = 'Error procesando la solicitud. Inténtalo de nuevo.';
        }

        aiMessage.content = `❌ **${errorMessage}**\n\n*Verifica que el servidor de Ollama esté ejecutándose en ${this.VITE_SERVER_BASE_URL}*\n\n${error.message || ''}`;
        aiMessage.formattedContent = this.md.render(aiMessage.content);
        aiMessage.isTyping = false;
        this.messages = [...this.messages];
        this.showErrorNotification(errorMessage);
      } finally {
        this.awaitingResponse = false;
        this.smoothScrollToBottom();
      }
    },

    copyMessage(content) {
      navigator.clipboard.writeText(content).then(() => {
        this.showSuccessNotification('Mensaje copiado al portapapeles');
      }).catch(err => {
        console.error('Error al copiar:', err);
        this.showErrorNotification('No se pudo copiar el mensaje');
      });
    },

    toggleSystemPrompt() {
      this.showSystemPrompt = !this.showSystemPrompt;
    },

    clearSystemPrompt() {
      this.systemPrompt = '';
      this.saveSystemPrompt(); // Immediately save the cleared state
    },

    usePresetPrompt() {
      this.systemPrompt = 'Eres un asistente útil que responde de manera concisa y clara. Siempre mantén un tono profesional y amigable.';
    },

    /**
     * Loads encrypted system prompt from localStorage
     */
    async loadSystemPrompt() {
      try {
        if (systemPromptCrypto.constructor.isSupported()) {
          const savedPrompt = await systemPromptCrypto.loadSystemPrompt();
          if (savedPrompt) {
            this.systemPrompt = savedPrompt;
          }
        } else {
          console.warn('Web Crypto API not supported, system prompts will not be persisted securely');
        }
      } catch (error) {
        console.warn('Failed to load system prompt:', error);
      }
    },

    /**
     * Saves encrypted system prompt to localStorage
     */
    async saveSystemPrompt() {
      try {
        if (systemPromptCrypto.constructor.isSupported()) {
          await systemPromptCrypto.saveSystemPrompt(this.systemPrompt);
        }
      } catch (error) {
        console.warn('Failed to save system prompt:', error);
      }
    },

    /**
     * Debounced save to avoid too frequent localStorage writes
     */
    debounceSaveSystemPrompt() {
      if (this.saveTimeout) {
        clearTimeout(this.saveTimeout);
      }
      this.saveTimeout = setTimeout(() => {
        this.saveSystemPrompt();
      }, 1000); // Save 1 second after user stops typing
    },

    showSuccessNotification(message) {
      // Simple notification system
      const notification = document.createElement('div');
      notification.className = 'notification success';
      notification.textContent = message;
      document.body.appendChild(notification);

      setTimeout(() => {
        notification.classList.add('show');
      }, 100);

      setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
          document.body.removeChild(notification);
        }, 300);
      }, 3000);
    },

    showErrorNotification(message) {
      const notification = document.createElement('div');
      notification.className = 'notification error';
      notification.textContent = message;
      document.body.appendChild(notification);

      setTimeout(() => {
        notification.classList.add('show');
      }, 100);

      setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
          document.body.removeChild(notification);
        }, 300);
      }, 5000);
    },

    createLineTransformer() {
      return new TransformStream({
        transformer: new class {
          constructor() {
            this.chunks = '';
          }

          transform(chunk, controller) {
            this.chunks += chunk;
            const lines = this.chunks.split(/(?=\n)/); // Split conservando delimitadores
            this.chunks = lines.pop() || '';
            lines.forEach(line => controller.enqueue(line));
          }

          flush(controller) {
            if (this.chunks) controller.enqueue(this.chunks);
          }
        }
      });
    },

    smoothScrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.chatBox;
        if (container) {
          container.scrollTo({
            top: container.scrollHeight,
            behavior: 'smooth'
          });
        }
      });
    },

    scrollToBottom() {
      this.$nextTick(() => {
        const container = this.$refs.chatBox;
        if (container) {
          container.scrollTop = container.scrollHeight;
        }
      });
    },
  }
}

// Transformador para dividir por líneas (NDJSON)
class LineBreakTransformer {
  constructor() {
    this.chunks = '';
  }

  transform(chunk, controller) {
    this.chunks += chunk;
    const lines = this.chunks.split('\n');
    this.chunks = lines.pop();
    lines.forEach(line => controller.enqueue(line));
  }

  flush(controller) {
    if (this.chunks) controller.enqueue(this.chunks);
  }
}
</script>

<style>
/* Import highlight.js theme */
@import 'highlight.js/styles/github-dark.css';

/* Estilos generales */
body {
  background-color: #292a2d;
  color: #f5f5f5;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  font-size: 16px;
  margin: 0;
  padding: 0;
  height: 100vh;
}

#app {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  width: 100%;
}

/* Contenedor principal */
.container {
  width: 100%;
  padding: 1rem;
}

/* Estilos del chat */
.chat {
  width: 100%;
  border-radius: 8px;
  background-color: #333;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  height: 90vh; /* Altura del chat */
  box-sizing: border-box; /* Asegura que el padding no afecte el ancho */
}

/* System Prompt Section */
.system-prompt-section {
  background-color: #2a2a2a;
  border-bottom: 1px solid #444;
  border-radius: 8px 8px 0 0;
}

.system-prompt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.8rem 1rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
  user-select: none;
}

.system-prompt-header:hover {
  background-color: rgba(255, 255, 255, 0.05);
}

.system-prompt-title {
  font-weight: 600;
  font-size: 0.9rem;
  color: #f5f5f5;
}

.toggle-icon {
  transition: transform 0.2s ease;
  font-size: 0.8rem;
  color: #888;
}

.toggle-icon.expanded {
  transform: rotate(180deg);
}

.system-prompt-container {
  padding: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.system-prompt-input {
  width: 100%;
  min-height: 80px;
  padding: 0.8rem;
  border: 1px solid #555;
  border-radius: 6px;
  background-color: #444;
  color: #f5f5f5;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  font-size: 0.9rem;
  resize: vertical;
  box-sizing: border-box;
  transition: border-color 0.2s ease;
}

.system-prompt-input:focus {
  outline: none;
  border-color: #4166d5;
  box-shadow: 0 0 0 2px rgba(65, 102, 213, 0.2);
}

.system-prompt-input::placeholder {
  color: #888;
  font-style: italic;
}

.system-prompt-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.8rem;
  justify-content: flex-end;
}

.clear-button, .preset-button {
  padding: 0.5rem 1rem;
  border: 1px solid #555;
  border-radius: 4px;
  background-color: #444;
  color: #f5f5f5;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.clear-button:hover {
  background-color: #dc3545;
  border-color: #dc3545;
}

.preset-button:hover {
  background-color: #4166d5;
  border-color: #4166d5;
}

.clear-button:disabled, .preset-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background-color: #444;
  border-color: #555;
}

.clear-button:disabled:hover, .preset-button:disabled:hover {
  background-color: #444;
  border-color: #555;
}

/* Contenedor de mensajes */
.chat-box {
  flex: 1;
  padding: 3rem;
  margin-bottom: 0.5rem;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: #444 #333;
  border-bottom: 1px solid #444;
  box-sizing: border-box; /* Asegura que el padding no afecte el ancho */
  scroll-behavior: smooth;
}

/* Estilos de los mensajes */
.message {
  margin-bottom: 1.5rem;
  padding: 1.2rem;
  border-radius: 12px;
  word-wrap: break-word;
  position: relative;
}

/* Header del mensaje */
.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.8rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.message-role {
  font-size: 0.9rem;
  font-weight: 600;
  opacity: 0.8;
}

/* Botón de copiar */
.copy-button {
  background: rgba(65, 102, 213, 0.2);
  border: 1px solid rgba(65, 102, 213, 0.3);
  color: #f5f5f5;
  padding: 0.4rem 0.6rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.8rem;
  transition: all 0.2s ease;
}

.copy-button:hover {
  background: rgba(65, 102, 213, 0.3);
  border-color: rgba(65, 102, 213, 0.5);
  transform: translateY(-1px);
}

.copy-button:active {
  transform: translateY(0);
}

/* Mensajes del usuario */
.user-message {
  background: linear-gradient(135deg, #41415850, #41415870);
  color: white;
  border-left: 3px solid #4166d5;
  margin-left: 2rem;
}

/* Mensajes del asistente */
.assistant-message {
  background: linear-gradient(135deg, rgba(34, 139, 34, 0.1), rgba(34, 139, 34, 0.05));
  color: white;
  border-left: 3px solid #22bb22;
  margin-right: 2rem;
}

/* Contenido del mensaje */
.message-content {
  line-height: 1.6;
}

/* Animación typewriter */
.typewriter {
  overflow: hidden;
  border-right: 2px solid #22bb22;
  animation: blink-caret 1.2s step-end infinite;
}

@keyframes blink-caret {
  from, to { border-color: transparent }
  50% { border-color: #22bb22 }
}

/* Indicador de escritura */
.typing-indicator {
  display: flex;
  gap: 4px;
  align-items: center;
  margin-top: 1rem;
  opacity: 0.7;
}

.typing-indicator .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #22bb22;
  animation: typing-dots 1.4s infinite ease-in-out;
}

.typing-indicator .dot:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator .dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing-dots {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1.2);
    opacity: 1;
  }
}

/* Pensamiento del asistente */
.message-think {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
  font-size: smaller;
}

/* Grupo de entrada de texto */
.input-group {
  display: flex;
  gap: 0.5rem;
  padding: 1rem;
  box-sizing: border-box;
}

/* Textarea */
textarea {
  flex: 1;
  padding: 0.9rem;
  border: none;
  border-radius: 4px;
  background-color: #555;
  color: white;
  resize: none;
  box-sizing: border-box;
  scrollbar-width: thin;
  scrollbar-color: #444 #555;
}

textarea:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(65, 102, 213, 0.3);
}

/* Botón de enviar */
button {
  padding: 0.9rem 1.5rem;
  background: #4166d5;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 500;
}

button:hover {
  background: #2f4f9f;
  transform: translateY(-1px);
}

button:disabled {
  background: #555;
  cursor: not-allowed;
  transform: none;
}

/* Estilos mejorados para markdown */
.message-content h1, .message-content h2, .message-content h3,
.message-content h4, .message-content h5, .message-content h6 {
  margin: 1.5rem 0 1rem 0;
  color: #fff;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  padding-bottom: 0.5rem;
}

.message-content h1 { font-size: 1.8rem; }
.message-content h2 { font-size: 1.5rem; }
.message-content h3 { font-size: 1.3rem; }

.message-content p {
  margin: 0.8rem 0;
  line-height: 1.7;
}

.message-content ul, .message-content ol {
  margin: 1rem 0;
  padding-left: 2rem;
}

.message-content li {
  margin: 0.5rem 0;
}

.message-content a {
  color: #4166d5;
  text-decoration: none;
  border-bottom: 1px solid transparent;
  transition: all 0.2s ease;
}

.message-content a:hover {
  border-bottom-color: #4166d5;
  color: #5577dd;
}

/* Estilos mejorados para código */
.message-content code {
  background: rgba(255, 255, 255, 0.1);
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
  font-size: 0.9rem;
  color: #ff6b6b;
}

.message-content pre {
  background: #1e1e1e !important;
  padding: 1.5rem !important;
  border-radius: 8px;
  overflow-x: auto;
  margin: 1.5rem 0;
  border: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
}

.message-content pre code {
  background: none !important;
  padding: 0 !important;
  color: #f8f8f2 !important;
  font-family: 'Fira Code', 'Monaco', 'Consolas', monospace;
  font-size: 0.9rem;
  line-height: 1.5;
}

/* Estilo para tablas */
.message-content table {
  border-collapse: collapse;
  width: 100%;
  margin: 1.5rem 0;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  overflow: hidden;
}

.message-content th, .message-content td {
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 0.8rem 1rem;
  text-align: left;
}

.message-content th {
  background: rgba(255, 255, 255, 0.1);
  font-weight: 600;
  color: #fff;
}

.message-content tr:nth-child(even) {
  background: rgba(255, 255, 255, 0.02);
}

/* Blockquotes */
.message-content blockquote {
  border-left: 4px solid #4166d5;
  margin: 1.5rem 0;
  padding: 1rem 1.5rem;
  background: rgba(65, 102, 213, 0.1);
  border-radius: 0 6px 6px 0;
  font-style: italic;
}

/* Notificaciones */
.notification {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 1rem 1.5rem;
  border-radius: 6px;
  color: white;
  font-weight: 500;
  z-index: 1000;
  transform: translateX(100%);
  transition: all 0.3s ease;
  min-width: 200px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.notification.success {
  background: linear-gradient(135deg, #22bb22, #28a745);
}

.notification.error {
  background: linear-gradient(135deg, #dc3545, #c82333);
}

.notification.show {
  transform: translateX(0);
}

/* Responsividad */
@media (max-width: 768px) {
  .container {
    padding: 0.5rem;
  }

  .message {
    margin-left: 0 !important;
    margin-right: 0 !important;
    padding: 1rem;
  }

  .chat-box {
    padding: 1rem;
  }
}
</style>