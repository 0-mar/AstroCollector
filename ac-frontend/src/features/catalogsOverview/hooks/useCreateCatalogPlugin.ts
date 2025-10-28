import {useMutation, useQueryClient} from "@tanstack/react-query";
import BaseApi from "@/features/common/api/baseApi.ts";
import {toast} from "sonner";
import type {CreatePluginDto, PluginDto} from "@/features/catalogsOverview/types.ts";
import {useAuth} from "@/features/common/auth/hooks/useAuth.ts";
import useUploadCatalogPlugin from "@/features/catalogsOverview/hooks/useUploadCatalogPlugin.ts";

const useCreateCatalogPlugin = () => {
    const queryClient = useQueryClient()
    const auth = useAuth()
    const uploadPluginMutation = useUploadCatalogPlugin()

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

export default useCreateCatalogPlugin;
