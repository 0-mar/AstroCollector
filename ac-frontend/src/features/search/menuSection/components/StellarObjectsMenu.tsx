import * as React from "react";
import type {Identifier, Identifiers} from "@/features/search/menuSection/types.ts";
import {Tabs, TabsContent, TabsList, TabsTrigger} from "../../../../../components/ui/tabs.tsx"
import ErrorAlert from "@/features/common/alerts/ErrorAlert.tsx";
import {useEffect, useContext, useMemo} from "react";
import {useQueries} from "@tanstack/react-query";
import BaseApi from "@/features/common/api/baseApi.ts";
import {IdentifiersContext} from "@/features/search/menuSection/components/IdentifiersContext.tsx";
import {SearchFormContext} from "@/features/search/searchSection/components/SearchFormContext.tsx";
import {MapPinCheckInside} from "lucide-react";
import {
    Tooltip,
    TooltipContent,
    TooltipTrigger,
} from "../../../../../components/ui/tooltip.tsx"
import {type PaginationResponse, type SubmitTaskDto, TaskStatus, type TaskStatusDto} from "@/features/common/api/types.ts";
import StellarObjectsTab from "@/features/search/menuSection/components/StellarObjectsTab.tsx";
import LoadingSkeleton from "@/features/common/loading/LoadingSkeleton.tsx";
import {Commet} from "react-loading-indicators";
import type {PluginDto} from "@/features/plugin/types.ts";

type StellarObjectsMenuProps = {
    pluginData: PluginDto[]
    setLightcurveSectionVisible: React.Dispatch<React.SetStateAction<boolean>>
};

const StellarObjectsMenu = ({
                                pluginData,
                                setLightcurveSectionVisible,
                            }: StellarObjectsMenuProps) => {

    const identifiersContext = useContext(IdentifiersContext);
    const searchFormContext = useContext(SearchFormContext)

    const endpoint = searchFormContext?.searchValues.objectName !== "" ? "find-object" : "cone-search"

    const taskQueries = useQueries({
        queries: pluginData.map(plugin => {
            const body = searchFormContext?.searchValues.objectName !== "" ?
                {name: searchFormContext?.searchValues.objectName, plugin_id: plugin.id} :
                {
                    right_ascension_deg: searchFormContext?.searchValues.rightAscension,
                    declination_deg: searchFormContext?.searchValues.declination,
                    radius: searchFormContext?.searchValues.radius,
                    plugin_id: plugin.id
                }

            return {
                queryKey: [`plugin_${plugin.id}`, searchFormContext?.searchValues],
                queryFn: () => BaseApi.post<SubmitTaskDto>("/tasks/submit-task/" + plugin.id + "/" + endpoint, body),
                staleTime: Infinity
            }
        })
    })

    const taskStatusQueries = useQueries({
        queries: pluginData.map((plugin, idx) => {
            return {
                queryKey: [`task_plugin_${plugin.id}`, searchFormContext?.searchValues],
                queryFn: () => {
                    // get task ID. The ID will be ALWAYS present, since the query starts only when the taskQuery was successful
                    const taskId = taskQueries[idx].data?.task_id
                    return BaseApi.get<TaskStatusDto>(`/tasks/task_status/${taskId}`)
                },
                refetchInterval: (query) => {
                    const data = query.state.data;
                    if (!data) {
                        return 1000;
                    }
                    return data.status === TaskStatus.COMPLETED || data.status === TaskStatus.FAILED ? false : 1000;
                },
                staleTime: Infinity,
                enabled: taskQueries[idx].isSuccess
            }
        })
    });

    // fetch results only when the task was successful
    const resultQueries = useQueries({
        queries: pluginData.map((plugin, idx) => {
            return {
                queryKey: [`task_plugin_${plugin.id}_results`, searchFormContext?.searchValues],
                queryFn: () => {
                    // get task ID. The ID will be ALWAYS present, since the query starts only when the taskQuery was successful
                    const taskId = taskQueries[idx].data?.task_id
                    return BaseApi.post<PaginationResponse<Identifier>>(`/retrieve/object-identifiers`, {filters: {task_id__eq: taskId}})
                },
                enabled: taskStatusQueries[idx].data?.status === TaskStatus.COMPLETED,
                staleTime: Infinity
            }
        }),
    })

    // filter task ids with fetched data
    const completedTasks = useMemo(() => {
        const ids = pluginData
            .map((_, idx) => {

                    return resultQueries[idx].isSuccess
                        ? [idx, taskQueries[idx].data?.task_id]
                        : null
                }
            )
            .filter((tuple) => {
                return tuple !== null;
            })

        return ids;
    }, [resultQueries.map(q => q.status).join(','),]);

    const ongoingTasks = useMemo(() => {
        return taskQueries.map((query, idx) => query.data?.task_id !== undefined ? [idx, query.data?.task_id] : undefined)
            .filter(tuple => tuple !== undefined)
            .filter(([idx, _]) => {
                for (const [idx2, _] of completedTasks) {
                    if (idx === idx2) return false;
                }
                return true;
            });
    }, [completedTasks]);

    // select all stellar objects that are within 0.1 arcsec or closer (must be the object we searched for)
    useEffect(() => {
        identifiersContext?.setSelectedObjectIdentifiers(prev => {
            const updatedState: Identifiers = {...prev};

            completedTasks.forEach(([idx, taskId]) => {
                const resultQuery = resultQueries[idx]
                if (!resultQuery.isSuccess) return;

                for (const dto of resultQuery.data?.data) {
                    if (dto.identifier.dist_arcsec <= 0.1) {
                        updatedState[dto.id] = dto.identifier;
                    }
                }
            })

            return updatedState;
        });
    }, [resultQueries.map(q => q.status).join(',')]);

    useEffect(() => {
        if (completedTasks.length === 0) {
            setLightcurveSectionVisible(false);
            return;
        }
        identifiersContext?.setLightCurveBtnDisabled(false);
        setLightcurveSectionVisible(true);
    }, [completedTasks]);

    useEffect(() => {
        if (Object.values(identifiersContext?.selectedObjectIdentifiers ?? {}).length === 0) {
            setLightcurveSectionVisible(false);
        } else {
            setLightcurveSectionVisible(true);
        }
    }, [identifiersContext?.selectedObjectIdentifiers]);

    if (pluginData.length === 0) {
        return <ErrorAlert title={"Database contains no catalogs"}
                           description={"Please contact the admins to add catalogs to the database."}/>
    }

    return (
        <>
            <div className="flex flex-row items-center gap-2 mb-4">
                <h2 className="text-xl font-medium text-gray-900">Search results by sources</h2>
                <Tooltip>
                    <TooltipTrigger asChild>
                        {ongoingTasks.length > 0 && <div>
                            <Commet color="#000" size="small" text="" textColor="" />
                        </div>}
                    </TooltipTrigger>
                    <TooltipContent>
                        {ongoingTasks.map(([idx, _]) => {
                            const plugin = pluginData[idx];
                            return (
                                <p key={`ongoing_${plugin.id}`}>Loading results from {plugin.name}</p>
                            )
                        })}
                    </TooltipContent>
                </Tooltip>
            </div>

            {completedTasks.length === 0 ? <LoadingSkeleton text={"Loading stellar objects..."}/> :
                <Tabs defaultValue={pluginData[0].id}>
                    <TabsList>
                        {completedTasks.map(([idx, taskId]) => {
                                const plugin = pluginData[idx];
                                if (resultQueries[idx].isSuccess && resultQueries[idx].data.count > 0) {
                                    return (
                                        <TabsTrigger key={`list_${plugin.id}`} value={plugin.id}>
                                            <Tooltip key={`list_${plugin.id}`}>
                                                <TooltipTrigger asChild>
                                    <span
                                        className="inline-flex items-center gap-1">{plugin.name}{plugin.directly_identifies_objects &&
                                        <MapPinCheckInside/>}</span>

                                                </TooltipTrigger>
                                                <TooltipContent>
                                                    {plugin.directly_identifies_objects ?
                                                        <p>Catalog groups data by stellar objects</p> :
                                                        <p>Catalog returns individual measurements</p>}
                                                </TooltipContent>
                                            </Tooltip>
                                        </TabsTrigger>
                                    )
                                }
                            }
                        )}

                    </TabsList>
                    {completedTasks.map(([idx, taskId]) => {
                            const plugin = pluginData[idx];
                            if (resultQueries[idx].isSuccess && resultQueries[idx].data.count > 0) {
                                return (
                                    <TabsContent key={`content_${plugin.id}`} value={plugin.id}>
                                        <StellarObjectsTab identifiers={resultQueries[idx].data.data}/>
                                    </TabsContent>
                                )
                            }
                        }
                    )}
                </Tabs>
            }
        </>
    )
}

export default StellarObjectsMenu;
