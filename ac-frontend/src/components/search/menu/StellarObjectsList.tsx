import type {Identifier, PluginDto, SearchValues, StellarObjectIdentifierDto} from "@/features/search/types.ts";
import type {Identifiers} from "@/features/search/menu/types.ts";
import * as React from "react";
import {useQuery} from "@tanstack/react-query";
import BaseApi from "@/features/api/baseApi.ts";
import LoadingSkeleton from "@/components/loading/LoadingSkeleton.tsx";
import LoadingError from "@/components/loading/LoadingError.tsx";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/../components/ui/table"
import {type PaginationResponse, type SubmitTaskDto, TaskStatus, type TaskStatusDto} from "@/features/api/types.ts";
import {useState} from "react";
import {Checkbox} from "@/../components/ui/checkbox"


type IdentifierCheckboxProps = {
    id: string,
    identifier: StellarObjectIdentifierDto,
    setSelectedObjectIdentifiers: React.Dispatch<React.SetStateAction<Identifiers>>,
    setLightCurveBtnDisabled: React.Dispatch<React.SetStateAction<boolean>>
};

const IdentifierCheckbox = ({
                                id,
                                identifier,
                                setSelectedObjectIdentifiers,
                                setLightCurveBtnDisabled
                            }: IdentifierCheckboxProps) => {
    const [checked, setChecked] = useState(false);

    const handleCheckedChange = (isChecked: boolean) => {
        setChecked(isChecked)
        setSelectedObjectIdentifiers((prevState) => {
            const updatedState: Identifiers = {...prevState}
            if (isChecked) {
                updatedState[id] = identifier
            } else {
                delete updatedState[id]
            }
            setLightCurveBtnDisabled(Object.keys(updatedState).length === 0)

            return updatedState
        })
    }

    return (
        <Checkbox
            id={id}
            checked={checked}
            onCheckedChange={handleCheckedChange}
        />
    )
}

type StellarObjectsListProps = {
    formData: SearchValues,
    plugin: PluginDto,
    setSelectedObjectIdentifiers: React.Dispatch<React.SetStateAction<Identifiers>>,
    setLightCurveBtnDisabled: React.Dispatch<React.SetStateAction<boolean>>
};

// TODO paginated tables!!!
const StellarObjectsList = ({
                                formData,
                                plugin,
                                setSelectedObjectIdentifiers,
                                setLightCurveBtnDisabled
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
        queryKey: [`plugin_${plugin.id}`],
        queryFn: () => BaseApi.post<SubmitTaskDto>("/tasks/submit-task/" + plugin.id + "/" + endpoint, body),
    })

    const taskStatusQuery = useQuery({
        queryKey: [`task_plugin_${plugin.id}`],
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
        enabled: taskQuery.isSuccess
    });

    const stellarObjectsResultsQuery = useQuery({
        queryKey: [`task_plugin_${plugin.id}_results`],
        queryFn: () => {
            // get task ID. The ID will be ALWAYS present, since the query starts only when the taskQuery was successful
            const taskId = taskQuery.data?.task_id
            return BaseApi.post<PaginationResponse<Identifier>>(`/retrieve/object-identifiers/${taskId}`, {task_id: taskId})
        },
        enabled: taskStatusQuery.data?.status === TaskStatus.COMPLETED
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
        <Table>
            <TableHeader>
                <TableRow>
                    <TableHead>Select</TableHead>
                    <TableHead>Right ascension (deg)</TableHead>
                    <TableHead>Declination (deg)</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {stellarObjectsResultsQuery.data.data.map((identifier) =>
                    <TableRow key={identifier.id}>
                        <TableCell>
                            <IdentifierCheckbox id={identifier.id} identifier={identifier.identifier}
                                                setSelectedObjectIdentifiers={setSelectedObjectIdentifiers}
                                                setLightCurveBtnDisabled={setLightCurveBtnDisabled}/>
                        </TableCell>
                        <TableCell>{identifier.identifier.ra_deg}</TableCell>
                        <TableCell>{identifier.identifier.dec_deg}</TableCell>
                    </TableRow>
                )}
            </TableBody>
        </Table>
    );

};

export default StellarObjectsList;
