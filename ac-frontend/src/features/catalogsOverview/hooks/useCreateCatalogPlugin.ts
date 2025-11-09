import {useMutation, useQueryClient} from "@tanstack/react-query";
import BaseApi from "@/features/common/api/baseApi.ts";
import {toast} from "sonner";
import type {CreatePluginDto, PluginDto} from "@/features/catalogsOverview/types.ts";
import {useAuth} from "@/features/common/auth/hooks/useAuth.ts";
import {fileContentType, uploadResources, uploadSrc} from "@/features/catalogsOverview/utils.ts";
import useProgress from "@/features/catalogsOverview/hooks/useProgress.ts";

type CreateCatalogPluginArgs = {
    createData: CreatePluginDto,
    file: File,
    resourcesFile: File | null
}

const useCreateCatalogPlugin = () => {
    const queryClient = useQueryClient()
    const auth = useAuth()
    const progress = useProgress()

    return {
        phase: progress.phase,
        overallProgress: progress.overallProgress,
        mutation: useMutation({
            onError: (_error) => {
                toast.error("Failed to create plugin. Please try again later.");
            },
            mutationFn: async ({createData, file, resourcesFile}: CreateCatalogPluginArgs) => {
                progress.setPhase("creating");
                progress.setSourceProgress(0);
                progress.setResourcesProgress(0);

                createData.created_by = auth?.user?.username ?? "system"
                const created = await BaseApi.post<PluginDto>(`/plugins`, createData)

                progress.setPhase("uploading_source");
                // upload sources
                try {
                    // 2) Upload source file (raw body)
                    progress.setPhase("uploading_source");
                    await uploadSrc(
                        file,
                        created.id,
                        progress.setSourceProgress
                    );

                    // 3) Upload resources (optional)
                    if (resourcesFile) {
                        progress.setPhase("uploading_resources");
                        await uploadResources(
                            `/plugins/upload-resources/${created.id}`,
                            resourcesFile,
                            // if you know it's zip, force it; otherwise fallback
                            fileContentType(resourcesFile, "application/zip"),
                            progress.setResourcesProgress
                        );
                    } else {
                        progress.setResourcesProgress(100)
                    }

                    progress.setPhase("done");
                    return created;
                } catch (err) {
                    // cleanup orphaned records
                    try {
                        await BaseApi.delete(`/plugins/${created.id}`);
                    } catch {
                        // ignore cleanup errors
                    }
                    throw err;
                }

            },
            onSuccess: async (createdPlugin) => {
                await queryClient.invalidateQueries({ queryKey: ["plugins"] });
                await queryClient.invalidateQueries({ queryKey: [`${createdPlugin.id}_resources`] });
                toast.success(`Plugin ${createdPlugin.name} created.`);
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

export default useCreateCatalogPlugin;
