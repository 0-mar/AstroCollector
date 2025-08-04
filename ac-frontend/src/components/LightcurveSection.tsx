import {useQueries} from "@tanstack/react-query";
import {axiosInstance} from "@/features/baseApi.ts";
import LightCurve from "@/components/LightCurve.tsx";

export default function LightcurveSection({selectedObjectIdentifiers}) {
    console.log(JSON.stringify(selectedObjectIdentifiers))
    const lightcurveTaskQueries = useQueries({
        queries: Object.keys(selectedObjectIdentifiers).map((id) => {
            const identifier = selectedObjectIdentifiers[id]
            return {
                queryKey: ['objectIdentifier', id],
                queryFn: () => axiosInstance.post(`/tasks/submit-task/${identifier.plugin_id}/photometric-data`, identifier),
            }
        }),
    });

    const allTasksResolved = lightcurveTaskQueries.every(
        (lcQuery) => lcQuery.isSuccess || lcQuery.isError
    );

    return (
        <>
            {lightcurveTaskQueries.some((lcQuery) => lcQuery.isLoading) ? (
                <p>Querying lightcurve data...</p>
            ) : null}
            {lightcurveTaskQueries.some((lcQuery) => lcQuery.isError) ? (
                <p>An error occured when querying lightcurve data retrieval task</p>
            ) : null}

            {allTasksResolved && (
                <LightCurve
                    taskIds={lightcurveTaskQueries
                        .filter((query) => query.isSuccess)
                        .map((query) => query.data.data.task_id)}
                />
            )}
        </>
    );
}
