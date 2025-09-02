import {useForm} from "react-hook-form";
import {yupResolver} from "@hookform/resolvers/yup";
import BaseApi from "@/features/api/baseApi.ts";
import {useQuery} from "@tanstack/react-query";

import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "@/../components/ui/form"
import {Input} from "@/../components/ui/input"
import SearchFormSubmitButton from "@/components/search/form/SearchFormSubmitButton.tsx";
import {formSchema, type PluginDto, type SearchValues} from "@/features/search/types.ts";
import type {PaginationResponse} from "@/features/api/types.ts";
import {useContext, useState} from "react";
import CoordsPanel from "@/components/search/form/CoordsPanel.tsx";
import {SearchFormContext} from "@/components/search/form/SearchFormContext.tsx";
import {ObjectCoordsContext} from "@/components/search/form/ObjectCoordsProvider.tsx";


const LabeledInput = ({label, ...props}) => {
    return (
        <div className={"flex gap-x-2 items-center"}>
            <Input className={"w-5/6"} placeholder={"e. g. 2.55"} {...props} />
            <span className={"w-1/6"}>{label}</span>
        </div>
    )
}


const SearchForm = ({setMenuVisible, setPluginData}) => {
    const searchFormContext = useContext(SearchFormContext)
    const objectCoordsContext = useContext(ObjectCoordsContext)

    const form = useForm<SearchValues>({
        resolver: yupResolver(formSchema),
        defaultValues: {
            objectName: "",
            rightAscension: "",
            declination: "",
            radius: ""
        },
    })


    const pluginQuery = useQuery({
        queryKey: ['plugins'],
        queryFn: () => BaseApi.post<PaginationResponse<PluginDto>>('/plugins/list', {}, {params: {
                offset: 0,
                count: 1000
            }}),
    })

    const onSubmit = (formData: SearchValues) => {
        setPluginData(pluginQuery.data?.data)
        setMenuVisible(true)
        searchFormContext?.setSearchValues(formData)

        if (formData.objectName !== "") {
            setCoordsPanelVisible(true)
        } else {
            setCoordsPanelVisible(false)
            objectCoordsContext?.setObjectCoords({declination: undefined, rightAscension: undefined})
        }
    }

    const [coordsPanelVisible, setCoordsPanelVisible] = useState(false)

    return (
        <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                <h2 className="text-lg font-medium text-gray-900">Search by object name</h2>
                <FormField
                    control={form.control}
                    name="objectName"
                    render={({field}) => (
                        <FormItem>
                            <FormLabel>Stellar object name</FormLabel>
                            <FormControl>
                                <Input placeholder="V Lep" {...field} />
                            </FormControl>
                            <FormMessage/>
                        </FormItem>
                    )}
                />
                {coordsPanelVisible && <CoordsPanel objectName={form.getValues("objectName") ?? ""} />}
                <h2 className="text-lg font-medium text-gray-900">Search by coordinates</h2>
                <FormField
                    control={form.control}
                    name="rightAscension"
                    render={({field}) => (
                        <FormItem>
                            <FormLabel>Right ascension</FormLabel>
                            <FormControl>
                                <LabeledInput label={"deg"} {...field}/>
                            </FormControl>
                            <FormMessage/>
                        </FormItem>
                    )}
                />
                <FormField
                    control={form.control}
                    name="declination"
                    render={({field}) => (
                        <FormItem>
                            <FormLabel>Declination</FormLabel>
                            <FormControl>
                                <LabeledInput label={"deg"} {...field}/>
                            </FormControl>
                            <FormMessage/>
                        </FormItem>
                    )}
                />
                <FormField
                    control={form.control}
                    name="radius"
                    render={({field}) => (
                        <FormItem>
                            <FormLabel>Radius</FormLabel>
                            <FormControl>
                                <LabeledInput label={"arcsec"} {...field}/>
                            </FormControl>
                            <FormMessage/>
                        </FormItem>
                    )}
                />
                {<p className="text-destructive text-sm">{form.formState.errors.global?.message}</p>}
                <SearchFormSubmitButton pluginQuery={pluginQuery}/>
            </form>
        </Form>
    )
}

export default SearchForm;
