import {useQuery} from "@tanstack/react-query";
import {useState} from "react";
import {axiosInstance} from "@/features/api/baseApi.ts";

const Checkbox = ({id, identifier, setSelectedObjects, setLightCurveBtnDisabled}) => {
    const [checked, setChecked] = useState(false);

    const handleCheckboxChange = (isChecked) => {
        setChecked(isChecked)
        setSelectedObjects((prevState) => {
            const updatedState = {...prevState}
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
        <input id={id} type="checkbox" checked={checked} onChange={(e) => handleCheckboxChange(e.target.checked)}/>
    )
}

export default function StellarObjects({taskId, setSelectedObjects, setLightCurveBtnDisabled}) {
    const taskStatusQuery = useQuery({
        queryKey: [taskId, "status"],
        queryFn: () => axiosInstance.get(`/tasks/task_status/${taskId}`),
        refetchInterval: (query) => {
            const data = query.state.data;
            if (!data) {
                return 1000;
            }
            return data.data.status === 'COMPLETED' ? false : 1000;
        },
    });

    const resultsQuery = useQuery({
        queryKey: [taskId, taskStatusQuery.data?.data.status, "results"],
        queryFn: () => axiosInstance.post(`/retrieve/object-identifiers/${taskId}`),
        enabled: taskStatusQuery.data?.data.status === 'COMPLETED'
    })

    return (
        <>
            {taskStatusQuery.data?.data.status === 'IN_PROGRESS' && <p>Querying for data in the catalog...</p>}
            {resultsQuery.isLoading && <p>Loading stellar objects...</p>}
            {resultsQuery.isError && <p>Failed to load stellar objects: {resultsQuery.error.message}</p>}
            {resultsQuery.isSuccess &&
                <table>
                    <thead>
                        <tr>
                            <th>Select</th>
                            <th>Right ascension</th>
                            <th>Declination</th>
                            <th>Additional data</th>
                        </tr>
                    </thead>
                    <tbody>
                        {resultsQuery.data?.data.data.map(stellarObject =>
                            <tr key={stellarObject.id}>
                                {/*<td><input id={"checkbox-" + stellarObject.id} type="checkbox" checked={false} onChange={e => handleCheckboxChange(e.target.checked, stellarObject.id, stellarObject.identifier)}/></td>*/}
                                <td><Checkbox id={stellarObject.id} identifier={stellarObject.identifier} setSelectedObjects={setSelectedObjects} setLightCurveBtnDisabled={setLightCurveBtnDisabled}/></td>
                                <td>{stellarObject.identifier.ra_deg}</td>
                                <td>{stellarObject.identifier.dec_deg}</td>
                            </tr>)}
                    </tbody>
                </table>
                }

        </>
    )
}
