import {useMutation, useQueryClient} from "@tanstack/react-query";
import BaseApi from "@/features/api/baseApi.ts";
import {toast} from "sonner";
import type {PluginDto, UpdatePluginDto} from "@/features/plugin/types.ts";
import useUploadPlugin from "@/features/plugin/useUploadPlugin.ts";

const useUpdatePlugin = (pluginId: string) => {
    const queryClient = useQueryClient()
    const uploadPluginMutation = useUploadPlugin()

    return useMutation({
        onError: (_error) => {
            toast.error("Failed to update plugin.")
        },
        mutationFn: async ({updateData, file}: { updateData: UpdatePluginDto, file: File | null }) => {
            const updated = await BaseApi.put<PluginDto>(`/plugins/${pluginId}`, updateData)
            return {updated, file}
        },
        onSuccess: async ({updated, file}) => {
            await queryClient.invalidateQueries({queryKey: ['plugins']})
            if (file !== null) {
                await uploadPluginMutation.mutateAsync({
                    pluginId: updated.id,
                    file: file
                })
            }
        },
        retry: (failureCount) => {
            return failureCount < 3;
        },
        retryDelay: (failureCount) => {
            return Math.min(1000 * 2 ** failureCount, 30000);
        },
    })
}

export default useUpdatePlugin;
