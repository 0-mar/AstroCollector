import type {PhotometricDataDto} from "@/features/search/photometricDataSection/types.ts";

export function lowerBound(data: PhotometricDataDto[], targetJd: number): number {
    let lo = 0, hi = data.length;
    while (lo < hi) {
        const mid = (lo + hi) >> 1;
        if (data[mid].julian_date < targetJd) {
            lo = mid + 1;
        }  else {
            hi = mid;
        }
    }
    return lo;
}

export function upperBound(data: PhotometricDataDto[], targetJd: number): number {
    let lo = 0, hi = data.length;

    while (lo < hi) {
        const mid = (lo + hi) >> 1;
        if (data[mid].julian_date <= targetJd) {
            lo = mid + 1;
        }  else {
            hi = mid;
        }
    }

    return lo;
}

// based on: https://github.com/sveinn-steinarsson/flot-downsample/
// thesis: https://skemman.is/handle/1946/15343
export function lttb(data: PhotometricDataDto[], start: number, end: number, threshold: number): PhotometricDataDto[] {
    const view = data.slice(start, end);
    const n = view.length;
    if (threshold >= n || threshold <= 0) return view;

    const out: PhotometricDataDto[] = new Array(threshold);
    out[0] = view[0];
    let a = 0;
    const every = (n - 2) / (threshold - 2);

    for (let i = 0; i < threshold - 2; i++) {
        const avgStart = Math.floor((i + 1) * every) + 1;
        const avgEnd   = Math.min(Math.floor((i + 2) * every) + 1, n);

        let avgX = 0, avgY = 0;
        const count = Math.max(1, avgEnd - avgStart);
        for (let j = avgStart; j < avgEnd; j++) {
            avgX += view[j].julian_date;
            avgY += view[j].magnitude;
        }
        avgX /= count; avgY /= count;

        const rangeStart = Math.min(Math.floor(i * every) + 1, n - 2);
        const rangeEnd   = Math.min(Math.floor((i + 1) * every) + 1, n - 1);

        const ax = view[a].julian_date, ay = view[a].magnitude;
        let maxArea = -1, nextA = rangeStart;
        for (let j = rangeStart; j < rangeEnd; j++) {
            const bx = view[j].julian_date, by = view[j].magnitude;
            const area = Math.abs((ax - avgX) * (by - ay) - (ax - bx) * (avgY - ay));
            if (area > maxArea) {
                maxArea = area; nextA = j;
            }
        }
        out[i + 1] = view[nextA];
        a = nextA;
    }
    out[threshold - 1] = view[n - 1];
    return out;
}
