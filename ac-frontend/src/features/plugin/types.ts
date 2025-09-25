import type {BaseDto} from "@/features/search/types.ts";

export type UpdatePluginDto = {
    name: string | null
    directly_identifies_objects: boolean | null
    description: string | null
    catalog_url: string | null
} & BaseDto

export type CreatePluginDto = {
    name: string
    directly_identifies_objects: boolean
    description: string
    catalog_url: string
    created_by: string
}
