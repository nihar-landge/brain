/**
 * E2E Encryption Utility (Phase 4.3)
 * Provides AES-GCM encryption for sensitive data like journal entries and chat messages.
 */

export const generateKey = async () => {
    return await window.crypto.subtle.generateKey(
        { name: "AES-GCM", length: 256 },
        true,
        ["encrypt", "decrypt"]
    );
};

export const exportKey = async (key) => {
    const exported = await window.crypto.subtle.exportKey("raw", key);
    return btoa(String.fromCharCode.apply(null, new Uint8Array(exported)));
};

export const importKey = async (keyString) => {
    const rawData = atob(keyString);
    const buffer = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) buffer[i] = rawData.charCodeAt(i);

    return await window.crypto.subtle.importKey(
        "raw", buffer,
        { name: "AES-GCM" },
        true, ["encrypt", "decrypt"]
    );
};

export const encryptText = async (text, key) => {
    const encoded = new TextEncoder().encode(text);
    const iv = window.crypto.getRandomValues(new Uint8Array(12));
    const ciphertext = await window.crypto.subtle.encrypt({ name: "AES-GCM", iv: iv }, key, encoded);

    const encryptedData = new Uint8Array(iv.length + new Uint8Array(ciphertext).byteLength);
    encryptedData.set(iv, 0);
    encryptedData.set(new Uint8Array(ciphertext), iv.length);

    return btoa(String.fromCharCode.apply(null, encryptedData));
};

export const decryptText = async (encryptedString, key) => {
    const rawData = atob(encryptedString);
    const encryptedData = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; i++) encryptedData[i] = rawData.charCodeAt(i);

    const iv = encryptedData.slice(0, 12);
    const ciphertext = encryptedData.slice(12);

    const decrypted = await window.crypto.subtle.decrypt({ name: "AES-GCM", iv: iv }, key, ciphertext);
    return new TextDecoder().decode(decrypted);
};
