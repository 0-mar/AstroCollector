import {useQueries} from "@tanstack/react-query";
import BaseApi from "@/features/api/baseApi.ts";
import {type SubmitTaskDto, TaskStatus, type TaskStatusDto} from "@/features/api/types.ts";
import type {PhotometricDataDto} from "@/features/search/lightcurve/types.ts";
import {useCallback, useContext, useEffect, useMemo, useState} from "react";
import {Tabs, TabsContent, TabsList, TabsTrigger} from "../../../../components/ui/tabs.tsx";
import LightCurvePlot from "@/components/search/photometricData/plot/LightCurvePlot.tsx";
import PlotOptionsPanel from "@/components/search/photometricData/plotOptions/PlotOptionsPanel.tsx";
import type {PluginDto, StellarObjectIdentifierDto} from "@/features/search/types.ts";
import {OptionsProvider} from "@/components/search/photometricData/plotOptions/OptionsContext.tsx";
import {RangeProvider} from "@/components/search/photometricData/plotOptions/CurrentRangeContext.tsx";
import PhotometricDataTable from "@/components/table/PhotometricDataTable.tsx";
import LoadingSkeleton from "@/components/loading/LoadingSkeleton.tsx";
import ErrorAlert from "@/components/alerts/ErrorAlert.tsx";
import PhaseCurvePlot from "@/components/search/photometricData/plot/PhaseCurvePlot.tsx";
import ExportDialog from "@/components/export/ExportDialog.tsx";
import PhotometryDataLoader from "@/components/search/photometricData/PhotometryDataLoader.tsx";
import {IdentifiersContext} from "@/components/search/menu/IdentifiersContext.tsx";


type PhotometricDataSectionProps = {
    pluginData: PluginDto[]
}


const PhotometricDataSection = ({pluginData}: PhotometricDataSectionProps) => {
    const identifiersContext = useContext(IdentifiersContext);
    const currentObjectIdentifiers = identifiersContext?.selectedObjectIdentifiers ?? {};

    const lightcurveTaskQueries = useQueries({
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
                    const taskId = lightcurveTaskQueries[idx].data?.task_id
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
                enabled: lightcurveTaskQueries[idx].isSuccess
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
                    ? lightcurveTaskQueries[idx].data?.task_id
                    : null
            )
            .filter((x): x is string => x !== null);
        return Array.from(new Set(ids)).sort();
    }, [taskStatusQueries.map(q => q.data?.status).join(','),
        lightcurveTaskQueries.map(q => q.data?.task_id).join(',')]);

    const [byTaskData, setByTaskData] = useState<Record<string, PhotometricDataDto[]>>({});

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

    const lightCurveData = useMemo(
        () => {
            return Object.values(byTaskData).flat();
        },
        [byTaskData]
    );


    return (
        <div className={"flex flex-col space-y-2"}>
            {completedTaskIds.map((taskId) => {
                return (
                    <PhotometryDataLoader key={taskId} taskId={taskId} onData={updateData(taskId)} />
                )
            })}
            <h2 className="text-lg font-medium text-gray-900">Photometric data</h2>
            <div>
                <ExportDialog readyData={Object.values(currentObjectIdentifiers).reduce((acc, identifier, idx) => {
                    const lq = lightcurveTaskQueries[idx];
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
                <TabsContent value="lightcurve">
                    <div className="grid grid-cols-1 gap-y-4">
                        <RangeProvider>
                            <OptionsProvider>
                                <PlotOptionsPanel/>
                                <LightCurvePlot pluginNames={pluginNames}
                                                lightCurveData={lightCurveData}></LightCurvePlot>
                            </OptionsProvider>
                        </RangeProvider>
                    </div>
                </TabsContent>
                <TabsContent value="phasecurve">
                    <div className="grid grid-cols-1 gap-y-4">
                        <RangeProvider>
                            <OptionsProvider>
                                <PlotOptionsPanel/>
                                <PhaseCurvePlot pluginNames={pluginNames}
                                                lightCurveData={lightCurveData}></PhaseCurvePlot>
                            </OptionsProvider>
                        </RangeProvider>
                    </div>
                </TabsContent>
                <TabsContent value="datatable">
                    <div className="bg-white rounded-md shadow-md">
                        <PhotometricDataTable
                            taskIds={completedTaskIds}
                            pluginNames={pluginNames}
                        />
                    </div>
                </TabsContent>
            </Tabs>
            <div>
                {Object.values(currentObjectIdentifiers).map((identifier, idx) => {
                    const dataTarget = `${identifier.ra_deg} ${identifier.dec_deg} (${pluginNames[identifier.plugin_id]})`
                    if (lightcurveTaskQueries[idx].isError) {
                        return (
                            <ErrorAlert
                                key={dataTarget}
                                title={"Photometric data query failed: " + dataTarget}
                                description={lightcurveTaskQueries[idx].error.message}/>
                        )
                    }
                    if (taskStatusQueries[idx].isError) {
                        return (
                            <ErrorAlert
                                key={dataTarget}
                                title={"Photometric data query failed: " + dataTarget}
                                description={taskStatusQueries[idx].error.message}/>
                        )
                    }
                    if (taskStatusQueries[idx].isPending || taskStatusQueries[idx].data?.status === TaskStatus.IN_PROGRESS) {
                        return (
                            <LoadingSkeleton
                                key={dataTarget}
                                text={"Loading photometric data for " + dataTarget}/>
                        )
                    }
                    if (taskStatusQueries[idx].data?.status === TaskStatus.FAILED) {
                        return (
                            <ErrorAlert
                                key={dataTarget}
                                title={"Failed to load photometric data for" + dataTarget}
                                description={"Job failed"}/>
                        )
                    }
                    if (taskStatusQueries[idx].isError) {
                        return (
                            <ErrorAlert
                                key={dataTarget}
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
