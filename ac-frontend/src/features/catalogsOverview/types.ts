import type {BaseDto} from "@/features/common/types.ts";

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
export type PluginDto = BaseDto & {
    name: string
    created_by: string
    created: string
    directly_identifies_objects: boolean
    catalog_url: string
    description: string
    file_name: string | null
}

export type Phase =
    | "idle"
    | "creating"
    | "uploading_source"
    | "uploading_resources"
    | "done";

export type Resources = {
    resources: string[]
}
