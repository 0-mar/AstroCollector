export const generateColor = () => {
    const digits = "0123456789abcdef"
    let color = "#"
    for (let i = 0; i < 6; i++) {
        color += digits[Math.floor(Math.random() * 16)]
    }
    return color
}

// Stable, deterministic color from plugin_id (no state needed)
function hashFNV1a(str: string) {
    let h = 0x811c9dc5; // FNV-1a 32-bit offset basis
    for (let i = 0; i < str.length; i++) {
        h ^= str.charCodeAt(i);
        h = Math.imul(h, 0x01000193); // FNV prime
    }
    return h >>> 0; // unsigned
}

export function colorFromId(id: string) {
    const hash = hashFNV1a(id);
    const hue = hash % 360;
    const sat = 55 + (hash % 20);      // 55–74%
    const light = 40 + ((hash >> 8) % 20); // 40–59%
    return `hsl(${hue}, ${sat}%, ${light}%)`;
}
