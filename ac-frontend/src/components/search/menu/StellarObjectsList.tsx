import type {Identifier} from "@/features/types.ts";
import {useQuery} from "@tanstack/react-query";
import BaseApi from "@/features/api/baseApi.ts";
import LoadingSkeleton from "@/components/loading/LoadingSkeleton.tsx";
import ErrorAlert from "@/components/alerts/ErrorAlert.tsx";
import {type PaginationResponse, type SubmitTaskDto, TaskStatus, type TaskStatusDto} from "@/features/api/types.ts";
import {identifierColumns} from "@/components/table/Columns.tsx";
import {ClientPaginatedDataTable} from "@/components/table/ClientPaginatedDataTable.tsx";
import {useContext, useEffect} from "react";
import {SearchFormContext} from "@/components/search/form/SearchFormContext.tsx";
import {IdentifiersContext} from "@/components/search/menu/IdentifiersContext.tsx";
import type {Identifiers} from "@/features/search/menu/types.ts";
import type {PluginDto} from "@/features/plugin/types.ts";

type StellarObjectsListProps = {
    plugin: PluginDto,
};

const StellarObjectsList = ({
                                plugin,
                            }: StellarObjectsListProps) => {
    const searchFormContext = useContext(SearchFormContext)
    const identifiersContext = useContext(IdentifiersContext)

    const body = searchFormContext?.searchValues.objectName !== "" ?
        {name: searchFormContext?.searchValues.objectName, plugin_id: plugin.id} :
        {
            right_ascension_deg: searchFormContext?.searchValues.rightAscension,
            declination_deg: searchFormContext?.searchValues.declination,
            radius: searchFormContext?.searchValues.radius,
            plugin_id: plugin.id
        }
    const endpoint = searchFormContext?.searchValues.objectName !== "" ? "find-object" : "cone-search"

    const taskQuery = useQuery({
        queryKey: [`plugin_${plugin.id}`, searchFormContext?.searchValues],
        queryFn: () => BaseApi.post<SubmitTaskDto>("/tasks/submit-task/" + plugin.id + "/" + endpoint, body),
        staleTime: Infinity
    })

    const taskStatusQuery = useQuery({
        queryKey: [`task_plugin_${plugin.id}`, searchFormContext?.searchValues],
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
        queryKey: [`task_plugin_${plugin.id}_results`, searchFormContext?.searchValues],
        queryFn: () => {
            // get task ID. The ID will be ALWAYS present, since the query starts only when the taskQuery was successful
            const taskId = taskQuery.data?.task_id
            return BaseApi.post<PaginationResponse<Identifier>>(`/retrieve/object-identifiers`, {task_id__eq: taskId})
        },
        enabled: taskStatusQuery.data?.status === TaskStatus.COMPLETED,
        staleTime: Infinity
    });

    useEffect(() => {
        if (!stellarObjectsResultsQuery.isSuccess) return;

        identifiersContext?.setSelectedObjectIdentifiers(prev => {
            const updatedState: Identifiers = {...prev};

            for (const dto of stellarObjectsResultsQuery.data?.data) {
                if (dto.identifier.dist_arcsec <= 0.1) {
                    updatedState[dto.id] = dto.identifier;
                }
            }

            return updatedState;
        });
    }, [stellarObjectsResultsQuery.isSuccess]);


    if (taskQuery.isPending) {
        return <LoadingSkeleton text={"Sending search query..."}/>
    }

    if (taskQuery.isError) {
        return <ErrorAlert title={"Search query failed"} description={taskQuery.error.message}/>
    }

    if (taskStatusQuery.isPending) {
        return <LoadingSkeleton text={"Waiting for search query to complete..."}/>
    }

    if (taskStatusQuery.isError) {
        return <ErrorAlert title={"Search query failed"} description={taskStatusQuery.error.message}/>
    }

    if (taskStatusQuery.isSuccess && taskStatusQuery.data?.status === TaskStatus.IN_PROGRESS) {
        return <LoadingSkeleton text={"Waiting for search query to complete..."}/>
    }

    if (taskStatusQuery.isSuccess && taskStatusQuery.data?.status === TaskStatus.FAILED) {
        return <ErrorAlert title={"Search query failed"} description={""}/>
    }

    if (stellarObjectsResultsQuery.isPending) {
        return <LoadingSkeleton text={"Loading stellar objects..."}/>
    }

    if (stellarObjectsResultsQuery.isError) {
        return <ErrorAlert title={"Failed to load stellar objects"}
                           description={stellarObjectsResultsQuery.error.message}/>
    }

    return (
        <>
            <span className={"font-bold"}>{stellarObjectsResultsQuery.data.total_items}</span> stellar object{stellarObjectsResultsQuery.data.total_items !== 1 ? "s" : ""} found
            <ClientPaginatedDataTable data={stellarObjectsResultsQuery.data.data} columns={identifierColumns} defaultSorting={[{id: "distance", desc: false}]}/>
        </>
    );

};

export default StellarObjectsList;
