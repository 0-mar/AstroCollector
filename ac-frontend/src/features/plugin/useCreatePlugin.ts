import {useMutation, useQueryClient} from "@tanstack/react-query";
import BaseApi from "@/features/api/baseApi.ts";
import {toast} from "sonner";
import type {CreatePluginDto, PluginDto} from "@/features/plugin/types.ts";
import {useAuth} from "@/features/auth/useAuth.ts";
import useUploadPlugin from "@/features/plugin/useUploadPlugin.ts";

const useCreatePlugin = () => {
    const queryClient = useQueryClient()
    const auth = useAuth()
    const uploadPluginMutation = useUploadPlugin()

    return useMutation({
        onError: (_error) => {
            toast.error("Failed to create plugin. Please try again later.");
        },
        mutationFn: async ({createData, file}: { createData: CreatePluginDto, file: File }) => {
            createData.created_by = auth?.user?.username ?? "system"
            const created = await BaseApi.post<PluginDto>(`/plugins`, createData)
            return {created, file}
        },
        onSuccess: async ({created, file}) => {
            await queryClient.invalidateQueries({queryKey: ['plugins']})
            await uploadPluginMutation.mutateAsync({
                pluginId: created.id,
                file: file
            })
        },
        retry: (failureCount) => {
            return failureCount < 3;
        },
        retryDelay: (failureCount) => {
            return Math.min(1000 * 2 ** failureCount, 30000);
        },
    })
}

export default useCreatePlugin;
