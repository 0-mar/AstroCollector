import {useQueries} from "@tanstack/react-query";
import BaseApi from "@/features/api/baseApi.ts";
import type {Identifiers} from "@/features/search/menu/types.ts";
import {type SubmitTaskDto, TaskStatus, type TaskStatusDto} from "@/features/api/types.ts";
import type {PhotometricDataDto} from "@/features/search/lightcurve/types.ts";
import {useEffect, useMemo, useState} from "react";
import type {PaginationResponse} from "@/features/api/types.ts";
import {Tabs, TabsContent, TabsList, TabsTrigger} from "../../../../components/ui/tabs.tsx";
import LightCurvePlot from "@/components/search/lightcurve/LightCurvePlot.tsx";
import LightCurveTable from "@/components/search/lightcurve/LightCurveTable.tsx";
import LightCurvePanel from "@/components/search/lightcurve/LightCurvePanel.tsx";
import type {PluginDto} from "@/features/search/types.ts";


type LightCurveSectionProps = {
    currentObjectIdentifiers: Identifiers
    pluginData: PluginDto[]
}


const LightCurveSection = ({currentObjectIdentifiers, pluginData}: LightCurveSectionProps) => {
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

    const resultQueries = useQueries({
        queries: Object.values(currentObjectIdentifiers).map((identifier, idx) => {
            return {
                queryKey: [`lcData_${identifier.plugin_id}_${identifier.ra_deg}_${identifier.dec_deg}`],
                queryFn: () => BaseApi.post<PaginationResponse<PhotometricDataDto>>(`/retrieve/photometric-data/${lightcurveTaskQueries[idx].data?.task_id}`, {task_id: lightcurveTaskQueries[idx].data?.task_id}),
                enabled: taskStatusQueries[idx].data?.status === TaskStatus.COMPLETED,
                staleTime: Infinity
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

    // TODO: Pagination
    const [lightCurveData, setLightCurveData] = useState<PhotometricDataDto[]>([])

    // FIXME: BUG: sometimes when changing between table and plot tabs and changing selected objects, after clicking Show lightcurve the data does not change
    useEffect(() => {
        const newData: PhotometricDataDto[] = [];
        resultQueries.forEach((resultQuery) => {
            if (resultQuery.isSuccess && resultQuery.data) {
                newData.push(...resultQuery.data.data)
            }
        });
        setLightCurveData((prevData) => {
            if (prevData.length == newData.length) {
                return prevData
            }
            return newData
        });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [resultQueries.map((q) => q.status).join(",")]);

    const [showErrorBars, setShowErrorBars] = useState(false)
    // TODO: Show errors/loading - but how exactly? As toasts or some kind of overlay?

    return (
        <>
            <Tabs defaultValue="lightcurve">
                <TabsList>
                    <TabsTrigger value="lightcurve">Light Curve</TabsTrigger>
                    <TabsTrigger value="datatable">Data table</TabsTrigger>
                </TabsList>
                <TabsContent value="lightcurve">
                    <LightCurvePanel showErrorBars={showErrorBars} setShowErrorBars={setShowErrorBars}/>
                    <LightCurvePlot showErrorBars={showErrorBars} pluginNames={pluginNames} lightCurveData={lightCurveData}></LightCurvePlot>
                </TabsContent>
                <TabsContent value="datatable">
                    <LightCurveTable lightCurveData={lightCurveData} />
                </TabsContent>
            </Tabs>
        </>
    )
}

export default LightCurveSection
