/**
 * Crypto utility for automatic encryption/decryption of system prompts
 * Uses Web Crypto API with domain-based key derivation
 */

class SystemPromptCrypto {
  constructor() {
    this.keyPromise = null;
  }

  /**
   * Derives a crypto key from the current domain origin
   * @returns {Promise<CryptoKey>}
   */
  async getDomainKey() {
    if (this.keyPromise) {
      return this.keyPromise;
    }

    this.keyPromise = this._deriveDomainKey();
    return this.keyPromise;
  }

  /**
   * Internal method to derive key from domain
   * @returns {Promise<CryptoKey>}
   * @private
   */
  async _deriveDomainKey() {
    try {
      const origin = window.location.origin;
      const encoder = new TextEncoder();
      
      // Create initial key material from domain
      const keyMaterial = await crypto.subtle.importKey(
        'raw',
        encoder.encode(origin),
        { name: 'PBKDF2' },
        false,
        ['deriveBits', 'deriveKey']
      );

      // Derive actual encryption key using PBKDF2
      const key = await crypto.subtle.deriveKey(
        {
          name: 'PBKDF2',
          salt: encoder.encode('ollama-webui-system-prompt'), // Fixed salt for deterministic key
          iterations: 100000,
          hash: 'SHA-256'
        },
        keyMaterial,
        { name: 'AES-GCM', length: 256 },
        false,
        ['encrypt', 'decrypt']
      );

      return key;
    } catch (error) {
      console.error('Failed to derive domain key:', error);
      throw new Error('Crypto key derivation failed');
    }
  }

  /**
   * Encrypts a system prompt string
   * @param {string} plaintext - The system prompt to encrypt
   * @returns {Promise<string>} Base64 encoded encrypted data
   */
  async encrypt(plaintext) {
    if (!plaintext || typeof plaintext !== 'string') {
      throw new Error('Invalid plaintext for encryption');
    }

    try {
      const key = await this.getDomainKey();
      const encoder = new TextEncoder();
      const data = encoder.encode(plaintext);
      
      // Generate random IV
      const iv = crypto.getRandomValues(new Uint8Array(12));
      
      // Encrypt the data
      const encrypted = await crypto.subtle.encrypt(
        { name: 'AES-GCM', iv: iv },
        key,
        data
      );

      // Combine IV and encrypted data
      const combined = new Uint8Array(iv.length + encrypted.byteLength);
      combined.set(iv);
      combined.set(new Uint8Array(encrypted), iv.length);

      // Return base64 encoded result
      return btoa(String.fromCharCode(...combined));
    } catch (error) {
      console.error('Encryption failed:', error);
      throw new Error('Failed to encrypt system prompt');
    }
  }

  /**
   * Decrypts an encrypted system prompt
   * @param {string} encryptedData - Base64 encoded encrypted data
   * @returns {Promise<string>} Decrypted system prompt
   */
  async decrypt(encryptedData) {
    if (!encryptedData || typeof encryptedData !== 'string') {
      throw new Error('Invalid encrypted data for decryption');
    }

    try {
      const key = await this.getDomainKey();
      
      // Decode base64
      const combined = new Uint8Array(
        atob(encryptedData).split('').map(c => c.charCodeAt(0))
      );

      // Extract IV and encrypted data
      const iv = combined.slice(0, 12);
      const encrypted = combined.slice(12);

      // Decrypt the data
      const decrypted = await crypto.subtle.decrypt(
        { name: 'AES-GCM', iv: iv },
        key,
        encrypted
      );

      // Convert back to string
      const decoder = new TextDecoder();
      return decoder.decode(decrypted);
    } catch (error) {
      console.error('Decryption failed:', error);
      throw new Error('Failed to decrypt system prompt');
    }
  }

  /**
   * Saves an encrypted system prompt to localStorage
   * @param {string} systemPrompt - The system prompt to save
   * @returns {Promise<void>}
   */
  async saveSystemPrompt(systemPrompt) {
    try {
      if (!systemPrompt || systemPrompt.trim() === '') {
        // Remove from localStorage if empty
        localStorage.removeItem('ollama-webui-system-prompt');
        return;
      }

      const encrypted = await this.encrypt(systemPrompt);
      localStorage.setItem('ollama-webui-system-prompt', encrypted);
    } catch (error) {
      console.warn('Failed to save encrypted system prompt:', error);
      // Fallback: save unencrypted for this session only
      // But don't persist to avoid security issues
    }
  }

  /**
   * Loads and decrypts system prompt from localStorage
   * @returns {Promise<string>} The decrypted system prompt, or empty string if none/failed
   */
  async loadSystemPrompt() {
    try {
      const encrypted = localStorage.getItem('ollama-webui-system-prompt');
      if (!encrypted) {
        return '';
      }

      return await this.decrypt(encrypted);
    } catch (error) {
      console.warn('Failed to load encrypted system prompt:', error);
      // Clear corrupted data
      localStorage.removeItem('ollama-webui-system-prompt');
      return '';
    }
  }

  /**
   * Check if crypto features are available
   * @returns {boolean}
   */
  static isSupported() {
    return (
      typeof crypto !== 'undefined' &&
      crypto.subtle &&
      typeof crypto.subtle.importKey === 'function' &&
      typeof crypto.subtle.deriveKey === 'function' &&
      typeof crypto.subtle.encrypt === 'function' &&
      typeof crypto.subtle.decrypt === 'function'
    );
  }
}

// Export singleton instance
const systemPromptCrypto = new SystemPromptCrypto();
export default systemPromptCrypto;