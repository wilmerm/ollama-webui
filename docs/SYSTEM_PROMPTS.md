# System Prompts (Custom Instructions) Feature

## Overview
The Ollama WebUI now supports **system prompts** (also known as custom instructions) that allow users to define the behavior and personality of the AI model at the beginning of conversations.

## How to Use

### 1. Accessing System Prompts
- Look for the **"⚙️ Instrucciones del Sistema"** section above the chat input area
- Click on it to expand/collapse the system prompt configuration

### 2. Setting a System Prompt
- **Manual Entry**: Type your custom instructions directly in the text area
- **Use Example**: Click the **"📋 Usar Ejemplo"** button to populate with a default prompt
- **Clear**: Click the **"🗑️ Limpiar"** button to clear the current system prompt

### 3. Example System Prompts

**IT Security Expert:**
```
You are an IT security expert. Always answer questions from a cybersecurity perspective and provide practical security recommendations.
```

**Spanish Tutor:**
```
You are a Spanish language tutor. Always respond in Spanish and provide explanations for grammar and vocabulary when helpful.
```

**Concise Assistant:**
```
You are a helpful assistant who answers concisely and clearly. Always maintain a professional and friendly tone.
```

## Technical Implementation

### Frontend Changes
- Added collapsible UI section for system prompt configuration
- Modified `sendPrompt()` method to include system messages in API calls
- System messages are automatically placed at the beginning of the conversation
- UI preserves system prompt when expanding/collapsing

### Backend Compatibility
- No backend changes needed - the existing API already supports system role messages
- System messages use the `"system"` role as defined in the Message model
- Fully backward compatible with existing conversations

### Message Flow
When a system prompt is configured:
1. **System message** (role: "system") - sent first
2. **Conversation history** (role: "user" and "assistant") - sent in order
3. **Current user message** (role: "user") - sent last

## Benefits

### For Users
- **Customize AI behavior** without modifying model files
- **Set context once** and maintain it throughout the conversation
- **Easy to modify** during conversations as needed
- **Optional feature** - works perfectly without system prompts

### For Developers
- **No breaking changes** - fully backward compatible
- **Leverages existing infrastructure** - no backend modifications needed
- **Clean UI integration** - matches existing design patterns
- **Extensible** - easy to add presets or additional functionality

## Examples of Use Cases

1. **Role-Playing**: "Act like a medieval knight and respond accordingly"
2. **Language Learning**: "Always respond in French and correct my grammar"
3. **Technical Expert**: "You are a Python developer expert, focus on best practices"
4. **Creative Writing**: "Help me write a story in the style of Edgar Allan Poe"
5. **Professional Context**: "You are a business consultant, provide actionable advice"

## Compatibility

- ✅ **Models**: Works with all Ollama models that support system prompts (most modern models)
- ✅ **Existing Conversations**: No impact on conversations without system prompts
- ✅ **API**: Compatible with existing Ollama API format
- ✅ **UI**: Responsive design works on desktop and mobile