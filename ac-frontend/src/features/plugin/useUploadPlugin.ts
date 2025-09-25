import {useMutation, useQueryClient} from "@tanstack/react-query";
import {toast} from "sonner";
import BaseApi from "@/features/api/baseApi.ts";
import type {PluginDto} from "@/features/search/types.ts";

const useUploadPlugin = () => {
    const queryClient = useQueryClient()
    return useMutation({
        onError: (_error) => {
            toast.error("Failed to upload plugin source code file. Please try again later.")
        },
        mutationFn: ({pluginId, file}: { pluginId: string, file: File }) => {
            const formData = new FormData();
            formData.append("plugin_file", file);
            return BaseApi.put<PluginDto>(`/plugins/upload/${pluginId}`, formData, {headers: {"Content-Type": "multipart/form-data"}})
        },
        onSuccess: async () => {
            await queryClient.invalidateQueries({queryKey: ['plugins']})
        },
        retry: (failureCount) => {
            return failureCount < 3;
        },
        retryDelay: (failureCount) => {
            return Math.min(1000 * 2 ** failureCount, 30000);
        },
    })
};

export default useUploadPlugin;
