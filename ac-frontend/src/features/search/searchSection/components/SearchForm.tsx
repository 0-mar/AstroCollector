import {useForm} from "react-hook-form";

import {
    Form,
    FormControl,
    FormField,
    FormItem,
    FormLabel,
    FormMessage,
} from "../../../../../components/ui/form.tsx"
import {Input} from "../../../../../components/ui/input.tsx"
import SearchFormSubmitButton from "@/features/search/searchSection/components/SearchFormSubmitButton.tsx";
import React, {useContext, useState} from "react";
import CoordsPanel from "@/features/search/searchSection/components/CoordsPanel.tsx";
import {SearchFormContext} from "@/features/search/searchSection/components/SearchFormContext.tsx";
import {ResolvedObjectCoordsContext} from "@/features/search/searchSection/components/ResolvedObjectCoordsProvider.tsx";
import {IdentifiersContext} from "@/features/search/menuSection/components/IdentifiersContext.tsx";
import useCatalogPluginsQuery from "@/features/catalogsOverview/hooks/useCatalogPlugins.ts";
import {searchFormSchema, type SearchFormValues} from "@/features/search/searchSection/schemas.ts";
import {zodResolver} from "@hookform/resolvers/zod";
import type {PluginDto} from "@/features/catalogsOverview/types.ts";
import {CircleQuestionMark} from "lucide-react";
import {Tooltip, TooltipContent, TooltipTrigger} from "../../../../../components/ui/tooltip.tsx";


const LabeledInput = ({label, placeholder, ...props}) => {
    return (
        <div className={"flex gap-x-2 items-center"}>
            <Input className={"w-5/6"} placeholder={placeholder} {...props} />
            <span className={"w-1/6"}>{label}</span>
        </div>
    )
}

type SearchFormProps = {
    setMenuVisible: React.Dispatch<React.SetStateAction<boolean>>,
    setLightcurveSectionVisible: React.Dispatch<React.SetStateAction<boolean>>,
    setPluginData: React.Dispatch<React.SetStateAction<PluginDto[]>>,
}

const SearchForm = ({setMenuVisible, setLightcurveSectionVisible, setPluginData}: SearchFormProps) => {
    const searchFormContext = useContext(SearchFormContext)
    const resolvedObjectCoordsContext = useContext(ResolvedObjectCoordsContext)
    const identifiersContext = useContext(IdentifiersContext)

    const form = useForm<SearchFormValues>({
        resolver: zodResolver(searchFormSchema),
        defaultValues: {
            objectName: "",
            rightAscension: "",
            declination: "",
            radius: ""
        },
    })


    const pluginQuery = useCatalogPluginsQuery()

    const onSubmit = (formData: SearchFormValues) => {
        setLightcurveSectionVisible(false)
        searchFormContext?.setSearchValues(formData)
        setPluginData(pluginQuery.data?.data ?? [])
        identifiersContext?.setSelectedObjectIdentifiers({})

        // show the resolved coordinates panel only when a stellar object was searched by its name
        if (formData.objectName !== "") {
            setCoordsPanelVisible(true)
        } else {
            setCoordsPanelVisible(false)
            // the "resolved" coords will be the ones searched by in this case
            // the search values will contain rightAscension and declination
            resolvedObjectCoordsContext?.setResolvedObjectCoords({rightAscension: searchFormContext?.searchValues?.rightAscension ?? -1, declination: searchFormContext?.searchValues?.declination ?? -95})
        }

        setMenuVisible(true)
    }

    const [coordsPanelVisible, setCoordsPanelVisible] = useState(false)

    return (
        <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
                <h2 className="text-xl font-medium text-gray-900">Search by object name</h2>
                <FormField
                    control={form.control}
                    name="objectName"
                    render={({field}) => (
                        <FormItem>
                            <FormLabel>
                                Stellar object name
                                <Tooltip>
                                    <TooltipTrigger asChild>
                                        <CircleQuestionMark />
                                    </TooltipTrigger>
                                    <TooltipContent>
                                        Resolve stellar object name using CDS. If the object is not found, use VSX for name resolution.
                                    </TooltipContent>
                                </Tooltip>
                            </FormLabel>
                            <FormControl>
                                <Input placeholder="V Lep" {...field} />
                            </FormControl>
                            <FormMessage/>
                        </FormItem>
                    )}
                />
                {coordsPanelVisible && <CoordsPanel/>}
                <h2 className="text-xl font-medium text-gray-900">Search by coordinates</h2>
                <FormField
                    control={form.control}
                    name="rightAscension"
                    render={({field}) => (
                        <FormItem>
                            <FormLabel>Right ascension</FormLabel>
                            <FormControl>
                                <LabeledInput placeholder={"92.744381"} label={"deg"} {...field}/>
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
                                <LabeledInput placeholder={"-20.211581"} label={"deg"} {...field}/>
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
                                <LabeledInput placeholder={"30"} label={"arcsec"} {...field}/>
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
