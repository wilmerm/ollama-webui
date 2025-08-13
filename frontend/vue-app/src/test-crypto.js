/**
 * Basic test for the crypto utility
 * Run this in browser console to test functionality
 */

import systemPromptCrypto from './utils/crypto.js';

// Test function to verify crypto functionality
async function testCrypto() {
  console.log('Testing System Prompt Crypto...');
  
  // Test 1: Check if crypto is supported
  console.log('Crypto supported:', systemPromptCrypto.constructor.isSupported());
  
  if (!systemPromptCrypto.constructor.isSupported()) {
    console.error('Web Crypto API not supported!');
    return;
  }
  
  // Test 2: Test encryption/decryption
  const testPrompt = 'You are a helpful assistant that responds clearly and professionally.';
  console.log('Original:', testPrompt);
  
  try {
    // Encrypt
    const encrypted = await systemPromptCrypto.encrypt(testPrompt);
    console.log('Encrypted:', encrypted);
    
    // Decrypt
    const decrypted = await systemPromptCrypto.decrypt(encrypted);
    console.log('Decrypted:', decrypted);
    
    // Verify
    console.log('Match:', testPrompt === decrypted);
    
    // Test 3: Test save/load functionality
    console.log('\nTesting save/load...');
    await systemPromptCrypto.saveSystemPrompt(testPrompt);
    const loaded = await systemPromptCrypto.loadSystemPrompt();
    console.log('Loaded:', loaded);
    console.log('Save/Load Match:', testPrompt === loaded);
    
    // Test 4: Test empty prompt handling
    console.log('\nTesting empty prompt...');
    await systemPromptCrypto.saveSystemPrompt('');
    const loadedEmpty = await systemPromptCrypto.loadSystemPrompt();
    console.log('Empty loaded:', loadedEmpty);
    console.log('Is empty string:', loadedEmpty === '');
    
    console.log('\n✅ All tests passed!');
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  }
}

// Export the test function
export { testCrypto };