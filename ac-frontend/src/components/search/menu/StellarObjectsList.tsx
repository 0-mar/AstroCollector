import type {Identifier, PluginDto, SearchValues} from "@/features/search/types.ts";
import {useQuery} from "@tanstack/react-query";
import BaseApi from "@/features/api/baseApi.ts";
import LoadingSkeleton from "@/components/loading/LoadingSkeleton.tsx";
import LoadingError from "@/components/loading/LoadingError.tsx";
import {type PaginationResponse, type SubmitTaskDto, TaskStatus, type TaskStatusDto} from "@/features/api/types.ts";
import {identifierColumns} from "@/components/table/Columns.tsx";
import {ClientPaginatedDataTable} from "@/components/table/ClientPaginatedDataTable.tsx";

type StellarObjectsListProps = {
    formData: SearchValues,
    plugin: PluginDto,
};

// TODO paginated tables!!!
const StellarObjectsList = ({
                                formData,
                                plugin,
                            }: StellarObjectsListProps) => {
    const body = formData.objectName !== "" ?
        {name: formData.objectName, plugin_id: plugin.id} :
        {
            right_ascension_deg: formData.rightAscension,
            declination_deg: formData.declination,
            radius: formData.radius,
            plugin_id: plugin.id
        }
    const endpoint = formData.objectName !== "" ? "find-object" : "cone-search"

    const taskQuery = useQuery({
        queryKey: [`plugin_${plugin.id}`, formData],
        queryFn: () => BaseApi.post<SubmitTaskDto>("/tasks/submit-task/" + plugin.id + "/" + endpoint, body),
        staleTime: Infinity
    })

    const taskStatusQuery = useQuery({
        queryKey: [`task_plugin_${plugin.id}`, formData],
        queryFn: () => {
            // get task ID. The ID will be ALWAYS present, since the query starts only when the taskQuery was successful
            const taskId = taskQuery.data?.task_id
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
        enabled: taskQuery.isSuccess
    });

    const stellarObjectsResultsQuery = useQuery({
        queryKey: [`task_plugin_${plugin.id}_results`, formData],
        queryFn: () => {
            // get task ID. The ID will be ALWAYS present, since the query starts only when the taskQuery was successful
            const taskId = taskQuery.data?.task_id
            return BaseApi.post<PaginationResponse<Identifier>>(`/retrieve/object-identifiers`, {task_id__eq: taskId})
        },
        enabled: taskStatusQuery.data?.status === TaskStatus.COMPLETED,
        staleTime: Infinity
    });


    if (taskQuery.isPending) {
        return <LoadingSkeleton text={"Sending search query..."}/>
    }

    if (taskQuery.isError) {
        return <LoadingError title={"Search query failed"} description={taskQuery.error.message}/>
    }

    if (taskStatusQuery.isPending) {
        return <LoadingSkeleton text={"Waiting for search query to complete..."}/>
    }

    if (taskStatusQuery.isError) {
        return <LoadingError title={"Search query failed"} description={taskStatusQuery.error.message}/>
    }

    if (taskStatusQuery.isSuccess && taskStatusQuery.data?.status === TaskStatus.IN_PROGRESS) {
        return <LoadingSkeleton text={"Waiting for search query to complete..."}/>
    }

    if (taskStatusQuery.isSuccess && taskStatusQuery.data?.status === TaskStatus.FAILED) {
        return <LoadingError title={"Search query failed"} description={""}/>
    }

    if (stellarObjectsResultsQuery.isPending) {
        return <LoadingSkeleton text={"Loading stellar objects..."}/>
    }

    if (stellarObjectsResultsQuery.isError) {
        return <LoadingError title={"Failed to load stellar objects"}
                             description={stellarObjectsResultsQuery.error.message}/>
    }

    return (
        <ClientPaginatedDataTable data={stellarObjectsResultsQuery.data.data} columns={identifierColumns}/>
        // <Table>
        //     <TableHeader>
        //         <TableRow>
        //             <TableHead>Select</TableHead>
        //             <TableHead>Right ascension (deg)</TableHead>
        //             <TableHead>Declination (deg)</TableHead>
        //         </TableRow>
        //     </TableHeader>
        //     <TableBody>
        //         {stellarObjectsResultsQuery.data.data.map((identifier) =>
        //             <TableRow key={identifier.id}>
        //                 <TableCell>
        //                     <IdentifierCheckbox id={identifier.id} identifier={identifier.identifier}/>
        //                 </TableCell>
        //                 <TableCell>{identifier.identifier.ra_deg}</TableCell>
        //                 <TableCell>{identifier.identifier.dec_deg}</TableCell>
        //             </TableRow>
        //         )}
        //     </TableBody>
        // </Table>
    );

};

export default StellarObjectsList;
