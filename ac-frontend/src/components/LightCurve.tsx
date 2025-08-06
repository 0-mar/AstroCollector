import {useQueries, useQuery} from "@tanstack/react-query";
import {useEffect, useState} from "react";
import {axiosInstance} from "@/features/api/baseApi.ts";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/../components/ui/tabs"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/../components/ui/table"
import LightCurvePlot from "@/components/LightCurvePlot.tsx";


export default function LightCurve({taskIds, objectIdentifiers}) {
    const taskStatusQueries = useQueries({
        queries: taskIds.map((taskId) => {
            return {
                queryKey: ['lcTaskStatus', taskId],
                queryFn: () => axiosInstance.get(`/tasks/task_status/${taskId}`),
                refetchInterval: (query) => {
                    const data = query.state.data;
                    if (!data) {
                        return 1000;
                    }
                    return data.data.status === 'COMPLETED' ? false : 1000;
                },
                staleTime: 1000 * 60 * 5
            }
        }),
    })

    // const resultQueries = useQueries({
    //     queries: taskIds.map((taskId, idx) => {
    //         return {
    //             queryKey: ['results', taskId, taskStatusQueries[idx].data?.data.status],
    //             queryFn: () => axiosInstance.post(`/retrieve/photometric-data/${taskId}`),
    //             enabled: taskStatusQueries[idx].data?.data.status === 'COMPLETED'
    //         }
    //     }),
    // })
    const resultQueries = useQueries({
        queries: objectIdentifiers.map((identifier, idx) => {
            return {
                queryKey: ['lcData', `${identifier.plugin_id}_${identifier.ra_deg}_${identifier.dec_deg}`],
                queryFn: () => axiosInstance.post(`/retrieve/photometric-data/${taskIds[idx]}`),
                enabled: taskStatusQueries[idx].data?.data.status === 'COMPLETED',
                staleTime: 1000 * 60 * 5
            }
        }),
    })

    const [lightCurveData, setLightCurveData] = useState<any[]>([])
    // useEffect(() => {
    //     resultQueries.forEach((resultQuery) => {
    //         if (resultQuery.isSuccess) {
    //             const newData = resultQuery.data?.data.data || [];
    //             setLightCurveData((prevData) => {
    //                 // Avoid adding the same data multiple times
    //                 if (!prevData.some((item) => newData.includes(item))) {
    //                     return [...prevData, ...newData];
    //                 }
    //                 return prevData;
    //             });
    //         }
    //     });
    // }, [resultQueries]); // Trigger effect when resultQueries change
    useEffect(() => {
        const newData = [];
        resultQueries.forEach((resultQuery) => {
            if (resultQuery.isSuccess && resultQuery.data) {
                newData.push(...resultQuery.data.data.data)
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
    //}, resultQueries.map((q) => q.data)); // ✅ Only rerun when any .data field changes

    return (
        <>
            <Tabs defaultValue="lightcurve">
                <TabsList>
                    <TabsTrigger value="lightcurve">Light Curve</TabsTrigger>
                    <TabsTrigger value="datatable">Data table</TabsTrigger>
                </TabsList>
                <TabsContent value="lightcurve">
                    <LightCurvePlot lightCurveData={lightCurveData}></LightCurvePlot>
                </TabsContent>
                <TabsContent value="datatable">
                    <Table>
                        <TableHeader>
                            <TableRow>
                                <TableHead>Julian Date</TableHead>
                                <TableHead>Magnitude</TableHead>
                                <TableHead>Magnitude error</TableHead>
                                <TableHead>Light filter</TableHead>
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {lightCurveData.map((lcData) =>
                                <TableRow>
                                    <TableCell>{lcData.julian_date}</TableCell>
                                    <TableCell>{lcData.magnitude}</TableCell>
                                    <TableCell>{lcData.magnitude_error}</TableCell>
                                    <TableCell>{lcData.light_filter === null ? '' : lcData.light_filter}</TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </TabsContent>
            </Tabs>
        </>
    )
}
