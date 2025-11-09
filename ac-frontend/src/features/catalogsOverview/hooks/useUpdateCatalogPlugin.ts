import {useMutation, useQueryClient} from "@tanstack/react-query";
import BaseApi from "@/features/common/api/baseApi.ts";
import {toast} from "sonner";
import type {PluginDto, UpdatePluginDto} from "@/features/catalogsOverview/types.ts";
import useProgress from "@/features/catalogsOverview/hooks/useProgress.ts";
import {fileContentType, uploadResources, uploadSrc} from "@/features/catalogsOverview/utils.ts";

type UpdateCatalogPluginArgs = {
    updateData: UpdatePluginDto,
    file: File | null,
    resourcesFile: File | null
}

const useUpdateCatalogPlugin = (pluginId: string) => {
    const queryClient = useQueryClient()
    const progress = useProgress()

    return {
        phase: progress.phase,
        overallProgress: progress.overallProgress,
        mutation: useMutation({
            onError: (_error) => {
                toast.error("Failed to update plugin.")
            },
            mutationFn: async ({updateData, file, resourcesFile}: UpdateCatalogPluginArgs) => {
                progress.setPhase("creating");
                progress.setSourceProgress(0);
                progress.setResourcesProgress(0);
                const updated = await BaseApi.put<PluginDto>(`/plugins/${pluginId}`, updateData)

                if (file !== null) {
                    progress.setPhase("uploading_source");
                    await uploadSrc(
                        file,
                        pluginId,
                        progress.setSourceProgress
                    );
                } else {
                    progress.setSourceProgress(100);
                }

                if (resourcesFile !== null) {
                    progress.setPhase("uploading_resources");
                    await uploadResources(
                        `/plugins/upload-resources/${pluginId}`,
                        resourcesFile,
                        // if you know it's zip, force it; otherwise fallback
                        fileContentType(resourcesFile, "application/zip"),
                        progress.setResourcesProgress
                    );
                } else {
                    progress.setResourcesProgress(100);
                }

                return updated
            },
            onSuccess: async (updatedPlugin) => {
                await queryClient.invalidateQueries({ queryKey: ["plugins"] });
                await queryClient.invalidateQueries({ queryKey: [`${updatedPlugin.id}_resources`] });
                toast.success(`Plugin ${updatedPlugin.name} updated.`);
            },
            retry: (failureCount) => {
                return failureCount < 3;
            },
            retryDelay: (failureCount) => {
                return Math.min(1000 * 2 ** failureCount, 30000);
            },
        })
    }
}

export default useUpdateCatalogPlugin;
