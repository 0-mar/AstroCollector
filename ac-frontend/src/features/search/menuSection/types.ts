import type {BaseDto} from "@/features/common/types.ts";

export type StellarObjectIdentifierDto = {
    plugin_id: string
    ra_deg: number
    dec_deg: number
    name: string
    dist_arcsec: number
    [key: string]: unknown
}

export type Identifier = BaseDto & {
    task_id: string
    identifier: StellarObjectIdentifierDto
}

export type Identifiers ={
    [key: string]: StellarObjectIdentifierDto
}
