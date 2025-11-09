import BaseApi from "@/features/common/api/baseApi.ts";
import type {PluginDto} from "@/features/catalogsOverview/types.ts";

export const fileContentType = (file: File, fallback: string) =>
    file?.type && file.type.trim().length > 0 ? file.type : fallback;

export const uploadResources = async (url: string, file: File, contentType: string, onPct?: (pct: number) => void) => {
    await BaseApi.put(url, file, {
        headers: {
            "Content-Type": contentType,
            "X-Filename": encodeURIComponent(file.name),
        },
        onUploadProgress: (e) => {
            if (typeof e.total === "number" && e.total > 0 && onPct) {
                const pct = Math.round((e.loaded / e.total) * 100);
                onPct(pct);
            }
        },
        timeout: 0, // disable axios timeout for big uploads
    });
};

export const uploadSrc = async (file: File, pluginId: string, onPct: (pct: number) => void) => {
    const formData = new FormData();
    formData.append("plugin_file", file);
    return await BaseApi.put<PluginDto>(`/plugins/upload/${pluginId}`, formData, {
        headers: {"Content-Type": "multipart/form-data"},
        onUploadProgress: (e) => {
            if (typeof e.total === "number" && e.total > 0 && onPct) {
                const pct = Math.round((e.loaded / e.total) * 100);
                onPct(pct);
            }
        },
        timeout: 0, // disable axios timeout for big uploads
    })
}
