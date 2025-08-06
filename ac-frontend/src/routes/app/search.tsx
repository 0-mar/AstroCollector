import {createFileRoute} from '@tanstack/react-router'
import {useForm} from "react-hook-form"
import {yupResolver} from "@hookform/resolvers/yup"
import * as yup from "yup"
import {useQuery} from '@tanstack/react-query';
import {useState} from "react";
import {axiosInstance} from "@/features/api/baseApi.ts";
import SubmitButton from "@/components/SubmitButton.tsx";
import StellarObjectsTable from "@/components/StellarObjectsTable.tsx";


export const Route = createFileRoute('/app/search')({
    component: SearchComponent,
})


const schema = yup
    .object({
        objectName: yup.string().nullable().transform((curr, orig) => (orig === "" ? null : curr)).min(1, "Object name must be at least 1 character long"),
        rightAscension: yup.number().nullable().transform((curr, orig) => (orig === "" ? null : curr)),
        declination: yup.number().nullable().transform((curr, orig) => (orig === "" ? null : curr)),
        radius: yup.number().nullable().transform((curr, orig) => (orig === "" ? null : curr)).integer().positive().min(1, "Radius must be at least 1 arcsec")
    })
    .test("name-or-coords", "Provide object name, or coordinates and radius", function (value) {
        const hasObjectName = value.objectName != null
        const hasCoords = value.rightAscension != null && value.declination != null && value.radius != null

        if ((hasObjectName && hasCoords) || (!hasObjectName && !hasCoords)) {
            return this.createError({
                message: 'Provide object name, or coordinates and radius',
                path: "global",
            });
        }
        return true;
    })

function SearchComponent() {
    const {
        register,
        handleSubmit,
        formState: {errors},
    } = useForm({
        resolver: yupResolver(schema)
    })

    const getPluginData = () => axiosInstance.post("/plugins/list", {}, {
        params: {
            offset: 0,
            count: 1000
        }
    })
    const pluginQuery = useQuery({
        queryKey: ['plugins'],
        queryFn: getPluginData
    })
    const [visible, setVisible] = useState(false)
    const [formData, setFormData] = useState(null)

    /*const submitAllTasks = async ({formData, pluginData}) => {
        const tasks = pluginData.map(plugin => {
            const body = formData.objectName
                ? { name: formData.objectName, plugin_id: plugin.id }
                : { right_ascension_deg: formData.rightAscension, declination_deg: formData.declination, radius: formData.radius, plugin_id: plugin.id };

            const urlSuffix = formData.objectName ? "/find-object" : "/cone-search";
            return axiosInstance.post(`/tasks/submit-task/${plugin.id}${urlSuffix}`, body);
        });

        return await Promise.allSettled(tasks);
    };

    const tasksMutation = useMutation({
        mutationFn: submitAllTasks
    })*/


    const onSubmit = (formData) => {
        /*tasksMutation.mutate({
            formData,
            pluginData: pluginQuery.data?.data.data
        })*/
        setVisible(true)
        setFormData(formData)
    }


    return (
        <>
            {/* "handleSubmit" will validate your inputs before invoking "onSubmit" */}
            <form onSubmit={handleSubmit(onSubmit)}>
                {/* register your input into the hook by invoking the "register" function */}
                <p>Search by object name</p>
                <input  {...register("objectName")} />
                <p>{errors.objectName?.message}</p>

                {/* include validation with required or other standard HTML validation rules */}
                <p>Search by coordinates</p>
                <input {...register("rightAscension")} />
                <p>{errors.rightAscension?.message}</p>
                {/* errors will return when field validation fails  */}
                {/*{errors.exampleRequired && <span>This field is required</span>}*/}
                <input {...register("declination")} />
                <p>{errors.declination?.message}</p>

                <input {...register("radius")} />
                <p>{errors.radius?.message}</p>

                <SubmitButton></SubmitButton>
                <p>{errors.global?.message}</p>
            </form>

            {/*{tasksMutation.isPending && <p>Querying search...</p>}*/}
            {/*{tasksMutation.isError && <p>Failed to query the search: {tasksMutation.error.message}</p>}*/}
            {/*{pluginQuery.isSuccess && tasksMutation.isSuccess && <StellarObjectsTable taskData={tasksMutation.data} pluginData={pluginQuery.data.data.data}></StellarObjectsTable>}*/}
            {pluginQuery.isSuccess && visible && <StellarObjectsTable formData={formData} pluginData={pluginQuery.data.data.data}></StellarObjectsTable>}
        </>
    )
}
