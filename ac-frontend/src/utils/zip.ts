export function zip<T1, T2>(array1: Array<T1>, array2: Array<T2>): Array<[T1, T2]> {
    const result: Array<[T1, T2]> = [];
    const length = Math.min(array1.length, array2.length);

    for (let i = 0; i < length; i++) {
        const e1 = array1[i];
        const e2 = array2[i];
        result.push([e1, e2]);
    }

    return result;
}
