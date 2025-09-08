import * as yup from "yup";
import type {InferType} from "yup";


const isNumberOrEmpty = (value: string | undefined) => {
    if (value === undefined || value === '') {
        return true;
    }
    return !isNaN(Number(value))
}

export const formSchema = yup
    .object({
        objectName: yup.string(),
        rightAscension: yup.string().test("checkRA", 'Right ascension must be a number', (value) => isNumberOrEmpty(value)),
        declination: yup.string().test("checkDec", 'Declination must be a number', (value) => isNumberOrEmpty(value)),
        radius: yup.string().test("checkRadius", 'Radius must be greater than zero', (value) => {
            const result = isNumberOrEmpty(value);
            if (!result) {
                return false;
            }

            if (value !== undefined && value.length > 0) {
                return Number(value) > 0;
            }

            return result
        })
    })
    .test("name-or-coords", "Provide object name, or coordinates and radius", function (value) {
        const hasObjectName = value.objectName !== ""
        const hasPartialCoords = value.rightAscension !== "" || value.declination !== "" || value.radius !== ""
        const hasAllCoords = value.rightAscension !== "" && value.declination !== "" && value.radius !== ""

        if ((hasObjectName && hasPartialCoords) || (!hasObjectName && !hasAllCoords)) {
            return this.createError({
                message: 'Provide object name, or coordinates and radius',
                path: "global",
            });
        }

        return true;
    })

export type SearchValues = InferType<typeof formSchema>

type BaseDto = {
    id: string
}

export type PluginDto = BaseDto & {
    name: string
    created_by: string
    created: string
    directly_identifies_objects: boolean
}

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
