export const isNumberOrEmpty = (value: string | undefined) => {
    if (value === undefined || value === '') {
        return true;
    }
    return !isNaN(Number(value))
}
