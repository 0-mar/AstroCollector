import {useQueries, useQuery} from "@tanstack/react-query";
import {axiosInstance} from "@/features/baseApi.ts";
import {useEffect, useState} from "react";

export default function LightCurve({taskIds}) {
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
            }
        }),
    })

    const resultQueries = useQueries({
        queries: taskIds.map((taskId, idx) => {
            return {
                queryKey: ['results', taskId, taskStatusQueries[idx].data?.data.status],
                queryFn: () => axiosInstance.post(`/retrieve/photometric-data/${taskId}`),
                enabled: taskStatusQueries[idx].data?.data.status === 'COMPLETED'
            }
        }),
    })

    const [lightCurveData, setLightCurveData] = useState<any[]>([])
    useEffect(() => {
        resultQueries.forEach((resultQuery) => {
            if (resultQuery.isSuccess) {
                const newData = resultQuery.data?.data.data || [];
                setLightCurveData((prevData) => {
                    // Avoid adding the same data multiple times
                    if (!prevData.some((item) => newData.includes(item))) {
                        return [...prevData, ...newData];
                    }
                    return prevData;
                });
            }
        });
    }, [resultQueries]); // Trigger effect when resultQueries change

    return (
        <>
            {lightCurveData.map(lcData => <p>{JSON.stringify(lcData)}</p>)}
        </>
    )
}
