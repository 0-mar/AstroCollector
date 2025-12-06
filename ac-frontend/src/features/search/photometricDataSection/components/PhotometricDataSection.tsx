import {useQueries} from "@tanstack/react-query";
import type {PhotometricDataDto} from "@/features/search/photometricDataSection/types.ts";
import {useCallback, useContext, useEffect, useMemo, useState} from "react";
import type {PluginDto} from "@/features/catalogsOverview/types.ts";
import { IdentifiersContext } from "../../menuSection/components/IdentifiersContext";
import BaseApi from "@/features/common/api/baseApi";
import {TaskStatus, type SubmitTaskDto, type TaskStatusDto } from "@/features/common/api/types";
import PhotometricDataLoader from "./PhotometricDataLoader";
import ExportDialog from "@/features/search/photometricDataSection/components/export/ExportDialog.tsx";
import type { StellarObjectIdentifierDto } from "../../menuSection/types";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/../components/ui/tabs";
import { ColorsProvider } from "./plotOptions/ColorsContext";
import { OptionsProvider } from "./plotOptions/OptionsContext";
import PlotOptionsPanel from "./plotOptions/PlotOptionsPanel";
import LightCurveGlPlot from "@/features/search/photometricDataSection/components/plot/LightCurveGlPlot.tsx";
import PhaseCurveGlPlot from "./plot/PhaseCurveGlPlot";
import PhotometricDataTable from "@/features/search/photometricDataSection/components/PhotometricDataTable.tsx";
import ErrorAlert from "@/features/common/alerts/ErrorAlert.tsx";
import LoadingSkeleton from "@/features/common/loading/LoadingSkeleton.tsx";
import ExportRawDataDialog from "@/features/search/photometricDataSection/components/export/ExportRawDataDialog.tsx";



type PhotometricDataSectionProps = {
    pluginData: PluginDto[]
}

export const unknownLightFilter = "Unknown"

const PhotometricDataSection = ({pluginData}: PhotometricDataSectionProps) => {
    const identifiersContext = useContext(IdentifiersContext);
    const currentObjectIdentifiers = identifiersContext?.selectedObjectIdentifiers ?? {};

    const photometricDataTaskQueries = useQueries({
        queries: Object.values(currentObjectIdentifiers).map((identifier) => {
            return {
                queryKey: [`objectIdentifier_${identifier.plugin_id}_${identifier.ra_deg}_${identifier.dec_deg}`],
                queryFn: () => BaseApi.post<SubmitTaskDto>(`/tasks/submit-task/${identifier.plugin_id}/photometric-data`, identifier),
                staleTime: Infinity
            }
        }),
    });

    // query status only of those tasks that were successfully submitted
    const taskStatusQueries = useQueries({
        queries: Object.values(currentObjectIdentifiers).map((identifier, idx) => {
            return {
                queryKey: [`lcTaskStatus_${identifier.plugin_id}_${identifier.ra_deg}_${identifier.dec_deg}`],
                queryFn: () => {
                    const taskId = photometricDataTaskQueries[idx].data?.task_id
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
                enabled: photometricDataTaskQueries[idx].isSuccess
            }
        }),
    })

    const pluginNames: Record<string, string> = useMemo(() => {
        const names: Record<string, string> = {};
        pluginData.forEach((plugin) => {
            names[plugin.id] = plugin.name;
        });
        return names;
    }, [pluginData])


    const completedTaskIds = useMemo(() => {
        const ids = Object.values(currentObjectIdentifiers)
            .map((_, idx) =>
                taskStatusQueries[idx].data?.status === TaskStatus.COMPLETED
                    ? photometricDataTaskQueries[idx].data?.task_id
                    : null
            )
            .filter((x): x is string => x !== null);
        return Array.from(new Set(ids)).sort();
    }, [taskStatusQueries.map(q => q.data?.status).join(','),
        photometricDataTaskQueries.map(q => q.data?.task_id).join(',')]);

    const taskUniqueLightFiltersQueries = useQueries({
        queries: Object.values(currentObjectIdentifiers).map((identifier, idx) => {
            return {
                queryKey: [`lightFilters_${identifier.plugin_id}_${identifier.ra_deg}_${identifier.dec_deg}`],
                queryFn: () => {
                    const taskId = photometricDataTaskQueries[idx].data?.task_id
                    return BaseApi.get<Array<string | null>>(`/retrieve/unique-light-filters/${taskId}`)
                },
                staleTime: Infinity,
                enabled: photometricDataTaskQueries[idx].isSuccess && taskStatusQueries[idx].data?.status === TaskStatus.COMPLETED
            }
        }),
    })

    // all unique light filters used in all tasks
    const taskUniqueLightFilters = useMemo(() => {
        const result = new Set<string>()
        const lightFilterArrays = taskUniqueLightFiltersQueries
            .map((_, idx) =>
                taskUniqueLightFiltersQueries[idx].isSuccess
                    ? taskUniqueLightFiltersQueries[idx].data
                    : null
            )
            .filter((x): x is Array<string | null> => x !== null);

        lightFilterArrays.forEach(array => {
            array.forEach(filter => {
                result.add(filter ?? unknownLightFilter)
            })
        })

        return Array.from(result).sort()
    }, [taskUniqueLightFiltersQueries.map(q => q.isSuccess).join(',')]);

    // mapping of task IDs with their corresponding photometric data
    const [byTaskData, setByTaskData] = useState<Record<string, PhotometricDataDto[]>>({});

    // keep track of all pluginIds used in the currently loaded data
    const currPluginIds = useMemo(() => {
        const result = new Set<string>();
        for (const data of Object.values(byTaskData)) {
            if (data.length > 0) {
                result.add(data[0].plugin_id)
            }
        }
        return result;
    }, [byTaskData])

    const updateData = useCallback((taskId: string) => (rows: PhotometricDataDto[]) => {
        setByTaskData(prev => {
            return { ...prev, [taskId]: rows }
        });
    }, []);

    // delete unchecked identifiers
    useEffect(() => {
        Object.keys(byTaskData).forEach(taskId => {
            if (!completedTaskIds.includes(taskId)) {
                setByTaskData(prevState => {
                    const newState = {...prevState};
                    delete newState[taskId];
                    return newState;
                })
            }
        })
    }, [completedTaskIds]);

    const photometricData = useMemo(
        () => {
            return Object.values(byTaskData).flat();
        },
        [byTaskData]
    );

    // mapping of ids to names of plugins the current data originates from
    // used as the legend
    const currPluginNames = useMemo(
        () => {
            const currPluginNames: Record<string, string> = {}
            for (const pluginId of currPluginIds) {
                currPluginNames[pluginId] = pluginNames[pluginId]
            }
            return currPluginNames
        },
        [currPluginIds]
    );

    return (
        <div className={"flex flex-col space-y-2"}>
            {completedTaskIds.map((taskId) => {
                return (
                    <PhotometricDataLoader key={taskId} taskId={taskId} onData={updateData(taskId)} />
                )
            })}
            <h2 className="text-xl font-medium text-gray-900">Photometric data</h2>
            <div className="flex flex-row gap-x-2">
                <ExportDialog readyData={Object.values(currentObjectIdentifiers).reduce((acc, identifier, idx) => {
                    const lq = photometricDataTaskQueries[idx];
                    const tq = taskStatusQueries[idx];

                    if (!lq?.isSuccess) return acc;
                    if (tq?.data?.status !== TaskStatus.COMPLETED) return acc;

                    acc.push([identifier, lq.data?.task_id]);
                    return acc;
                }, [] as Array<[StellarObjectIdentifierDto, string]>)} pluginNames={pluginNames}/>
                <ExportRawDataDialog readyData={Object.values(currentObjectIdentifiers).reduce((acc, identifier, idx) => {
                    const lq = photometricDataTaskQueries[idx];
                    const tq = taskStatusQueries[idx];

                    if (!lq?.isSuccess) return acc;
                    if (tq?.data?.status !== TaskStatus.COMPLETED) return acc;

                    acc.push([identifier, lq.data?.task_id]);
                    return acc;
                }, [] as Array<[StellarObjectIdentifierDto, string]>)} pluginNames={pluginNames}/>
            </div>
            <Tabs defaultValue="lightcurve">
                <TabsList>
                    <TabsTrigger value="lightcurve">Light Curve</TabsTrigger>
                    <TabsTrigger value="phasecurve">Phase Curve</TabsTrigger>
                    <TabsTrigger value="datatable">Data table</TabsTrigger>
                </TabsList>
                <ColorsProvider currPluginNames={currPluginNames} currLightFilters={taskUniqueLightFilters}>
                    <TabsContent value="lightcurve">
                        <div className="flex flex-col gap-y-4">
                            <OptionsProvider>
                                <PlotOptionsPanel pluginNames={currPluginNames} lightFilters={taskUniqueLightFilters}/>
                                <LightCurveGlPlot data={photometricData} pluginNames={currPluginNames}></LightCurveGlPlot>
                            </OptionsProvider>
                        </div>
                    </TabsContent>
                    <TabsContent value="phasecurve">
                        <div className="grid grid-cols-1 gap-y-4">
                            <OptionsProvider>
                                <PlotOptionsPanel pluginNames={currPluginNames} lightFilters={taskUniqueLightFilters}/>
                                <PhaseCurveGlPlot data={photometricData}
                                                  pluginNames={currPluginNames} />
                            </OptionsProvider>
                        </div>
                    </TabsContent>
                </ColorsProvider>
                <TabsContent value="datatable">
                    <div className="bg-white rounded-md shadow-md">
                        <PhotometricDataTable
                            taskIds={completedTaskIds}
                            pluginNames={pluginNames}
                        />
                    </div>
                </TabsContent>
            </Tabs>
            <div className="flex flex-col gap-y-4">
                {Object.values(currentObjectIdentifiers).map((identifier, idx) => {
                    const targetName = identifier.name !== null ? ` (${identifier.name})` : ''
                    const dataTarget = `${identifier.ra_deg} ${identifier.dec_deg}` + targetName + ` [${pluginNames[identifier.plugin_id]}]`
                    if (photometricDataTaskQueries[idx].isError) {
                        return (
                            <ErrorAlert
                                key={dataTarget + `${identifier.plugin_id}`}
                                title={"Photometric data query failed: " + dataTarget}
                                description={photometricDataTaskQueries[idx].error.message}/>
                        )
                    }
                    if (taskStatusQueries[idx].isError) {
                        return (
                            <ErrorAlert
                                key={dataTarget + `${identifier.plugin_id}`}
                                title={"Photometric data query failed: " + dataTarget}
                                description={taskStatusQueries[idx].error.message}/>
                        )
                    }
                    if (taskStatusQueries[idx].isPending || taskStatusQueries[idx].data?.status === TaskStatus.IN_PROGRESS) {
                        return (
                            <LoadingSkeleton
                                key={dataTarget + `${identifier.plugin_id}`}
                                text={"Loading photometric data for " + dataTarget}/>
                        )
                    }
                    if (taskStatusQueries[idx].data?.status === TaskStatus.FAILED) {
                        return (
                            <ErrorAlert
                                key={dataTarget + `${identifier.plugin_id}`}
                                title={"Failed to load photometric data for " + dataTarget}
                                description={"Job failed"}/>
                        )
                    }
                    if (taskStatusQueries[idx].isError) {
                        return (
                            <ErrorAlert
                                key={dataTarget + `${identifier.plugin_id}`}
                                title={"Photometric data query failed: " + dataTarget}
                                description={taskStatusQueries[idx].error.message}/>
                        )
                    }
                })}
            </div>
        </div>
    )
}

export default PhotometricDataSection
