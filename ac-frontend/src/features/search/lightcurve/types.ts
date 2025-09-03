export type PhotometricDataDto = {
    plugin_id: string
    julian_date: number
    magnitude: number
    magnitude_error: number
    light_filter: string | null
}

export type PhaseCurveDataDto = {
    period: number | null
    epoch: number | null
    ra_deg: number | null
    dec_deg: number | null
    vsx_object_name: string | null
}
