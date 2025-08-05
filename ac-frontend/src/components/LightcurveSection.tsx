import {useQueries} from "@tanstack/react-query";
import {axiosInstance} from "@/features/baseApi.ts";
import LightCurve from "@/components/LightCurve.tsx";
import {zip} from "@/utils/zip.ts";

export default function LightcurveSection({selectedObjectIdentifiers}) {
    const lightcurveTaskQueries = useQueries({
        queries: Object.values(selectedObjectIdentifiers).map((identifier) => {
            return {
                queryKey: ['objectIdentifier', `${identifier.plugin_id}_${identifier.ra_deg}_${identifier.dec_deg}`],
                queryFn: () => axiosInstance.post(`/tasks/submit-task/${identifier.plugin_id}/photometric-data`, identifier),
                staleTime: 1000 * 60 * 5
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
                    objectIdentifiers={zip(lightcurveTaskQueries, Object.values(selectedObjectIdentifiers))
                        .filter(([query, identifier]) => query.isSuccess)
                        .map(([query, identifier]) => identifier)}
                />
            )}
        </>
    );
}
