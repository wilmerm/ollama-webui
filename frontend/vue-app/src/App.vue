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
          <div class="message-content" v-html="msg.formattedContent || msg.content"></div>
          <div v-if="index === messages.length - 1 && awaitingResponse" class="typing-indicator">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
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

export default {
  data() {
    return {
      prompt: '',
      messages: [],
      md: markRaw(new MarkdownIt()),
      awaitingResponse: false,
      currentStream: null,
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
      };
      this.messages.push(aiMessage);

      try {
        const response = await fetch('http://localhost:8000/api/ollama', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            messages: this.messages
              .slice(0, -1)
              .map(msg => ({ role: msg.role, content: msg.content })),
            stream: true
          })
        });

        if (!response.ok) {
          throw new Error(await response.text());
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
                    this.scrollToBottom();
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

      } catch (error) {
        console.error('Error:', error);
        aiMessage.content = `Error: ${error.message}`;
        aiMessage.formattedContent = this.md.render(aiMessage.content);
        this.messages = [...this.messages];
      } finally {
        this.awaitingResponse = false;
      }
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
}

/* Estilos de los mensajes */
.message {
  margin-bottom: 0.1rem;
  padding: 1rem;
  border-radius: 12px;
  word-wrap: break-word;
}

/* Mensajes del usuario */
.user-message {
  background-color: #41415850;
  color: white;
  align-self: flex-end;
  display: inline-block;
}

/* Mensajes del asistente */
.assistant-message {
  background-color: transparent;
  color: white;
  align-self: flex-start;
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
}

/* Botón de enviar */
button {
  padding: 0.9rem 1.5rem;
  background: #4166d5;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background 0.3s ease;
}

button:hover {
  background: #2f4f9f;
}

button:disabled {
  background: #555;
  cursor: not-allowed;
}

/* Estilos para markdown (opcional) */
.markdown-content {
  margin-top: 0.5rem;
}

.markdown-content h1, .markdown-content h2, .markdown-content h3 {
  margin: 1rem 0;
}

.markdown-content p {
  margin: 0.5rem 0;
}

.markdown-content ul, .markdown-content ol {
  margin: 0.5rem 0;
  padding-left: 1.5rem;
}

.markdown-content code {
  background: #f0f0f0;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  font-family: monospace;
}

.markdown-content pre {
  background: #f5f5f5;
  padding: 1rem;
  border-radius: 6px;
  overflow-x: auto;
  margin: 1rem 0;
}

.markdown-content pre code {
  background: none;
  padding: 0;
}

/* Aplicar estilo al contenido */
</style>