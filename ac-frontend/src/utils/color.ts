export const generateColor = () => {
    const digits = "0123456789abcdef"
    let color = "#"
    for (let i = 0; i < 6; i++) {
        color += digits[Math.floor(Math.random() * 16)]
    }
    return color
}

// deterministic color from a string
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

export const COLORS: [number, number, number][] = [
    [28, 15, 179],
    [179, 15, 15],
    [166, 15, 179],
    [11, 142, 32],
    [179, 15, 94],
    [93, 132, 11],
    [14, 132, 170],
    [179, 94, 15],
    [15, 41, 179],
    [11, 142, 95],
    [179, 15, 133],
    [122, 132, 11],
    [67, 15, 179],
    [11, 142, 17],
    [15, 120, 179],
    [146, 15, 179],
    [179, 74, 15],
    [179, 15, 34],
    [69, 142, 11],
    [15, 61, 179],
    [11, 142, 79],
    [170, 107, 14],
    [11, 142, 110],
    [15, 100, 179],
    [132, 127, 11],
    [107, 15, 179],
    [179, 34, 15],
    [179, 15, 113],
    [53, 142, 11],
    [11, 132, 132],
    [127, 15, 179],
    [160, 119, 13],
    [179, 15, 153],
    [37, 142, 11],
    [47, 15, 179],
    [179, 54, 15],
    [22, 142, 11],
    [15, 80, 179],
    [11, 142, 63],
    [79, 132, 11],
    [179, 15, 54],
    [142, 121, 11],
    [15, 21, 179],
    [11, 142, 48],
    [108, 132, 11],
    [179, 15, 173],
    [12, 134, 151],
    [11, 142, 126],
    [179, 15, 74],
    [87, 15, 179],
];
