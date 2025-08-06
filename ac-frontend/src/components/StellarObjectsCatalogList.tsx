import '../styles.css'
import {useQuery} from "@tanstack/react-query";
import {axiosInstance} from "@/features/api/baseApi.ts";
import StellarObjects from "@/components/StellarObjects.tsx";

export default function StellarObjectsCatalogList({formData, plugin, setSelectedObjects, setLightCurveBtnDisabled}) {
    const body = formData.objectName != null ? {name: formData.objectName, plugin_id: plugin.id} : {right_ascension_deg: formData.rightAscension, declination_deg: formData.declination, radius: formData.radius, plugin_id: plugin.id}
    const endpoint = formData.objectName != null ? "find-object" : "cone-search"
    const taskQuery = useQuery({
        queryKey: [`plugin_${plugin.id}`, formData],
        queryFn: () => axiosInstance.post("/tasks/submit-task/" + plugin.id + "/" + endpoint, body),
        enabled: !!formData
    })

    return (
        <>
            <h2>{plugin.name}</h2>
            {taskQuery.isPending && <p>Sending search task...</p>}
            {taskQuery.isError && <p>Failed to query the tasks: {taskQuery.error.message}</p>}
            {taskQuery.isSuccess && <StellarObjects taskId={taskQuery.data.data.task_id} setSelectedObjects={setSelectedObjects} setLightCurveBtnDisabled={setLightCurveBtnDisabled}></StellarObjects>}
        </>
    )
}
