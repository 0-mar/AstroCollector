export type PhotometricDataDto = {
    plugin_id: string
    julian_date: number
    magnitude: number
    magnitude_error: number
    light_filter: string | null
}
