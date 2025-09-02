export type PhotometricDataDto = {
    plugin_id: string
    julian_date: number
    magnitude: number
    magnitude_error: number
    light_filter: string | null
}

export type PhaseCurveDataDto = {
    period: number | undefined
    epoch: number | undefined
    ra_deg: number | undefined
    dec_deg: number | undefined
    vsx_object_name: string | undefined
}
