import type {PluginDto} from "@/features/search/types.ts";
import * as React from "react";
import type {Identifiers} from "@/features/search/menu/types.ts";
import {Tabs, TabsContent, TabsList, TabsTrigger} from "@/../components/ui/tabs"
import StellarObjectsList from "@/components/search/menu/StellarObjectsList.tsx";
import {Button} from "@/../components/ui/button"
import ErrorAlert from "@/components/alerts/ErrorAlert.tsx";
import {useEffect, useContext} from "react";
import {useQueryClient} from "@tanstack/react-query";
import BaseApi from "@/features/api/baseApi.ts";
import {IdentifiersContext} from "@/components/search/menu/IdentifiersContext.tsx";
import {SearchFormContext} from "@/components/search/form/SearchFormContext.tsx";

type StellarObjectsMenuProps = {
    pluginData: PluginDto[]
    setLightcurveSectionVisible: React.Dispatch<React.SetStateAction<boolean>>
    setCurrentObjectIdentifiers: React.Dispatch<React.SetStateAction<Identifiers>>
};

const StellarObjectsMenu = ({
                                pluginData,
                                setLightcurveSectionVisible,
                                setCurrentObjectIdentifiers
                            }: StellarObjectsMenuProps) => {

    const identifiersContext = useContext(IdentifiersContext);
    const searchFormContext = useContext(SearchFormContext)

    const queryClient = useQueryClient();
    useEffect(() => {
        pluginData.forEach(plugin => {
            console.log("Prefetching plugin", plugin.id);
            const body = searchFormContext?.searchValues.objectName !== "" ?
                {name: searchFormContext?.searchValues.objectName, plugin_id: plugin.id} :
                {
                    right_ascension_deg: searchFormContext?.searchValues.rightAscension,
                    declination_deg: searchFormContext?.searchValues.declination,
                    radius: searchFormContext?.searchValues.radius,
                    plugin_id: plugin.id
                };

            const endpoint = searchFormContext?.searchValues.objectName !== "" ? "find-object" : "cone-search";

            // Prefetch Submit Task (same as taskQuery)
            queryClient.prefetchQuery({
                queryKey: [`plugin_${plugin.id}`, searchFormContext?.searchValues],
                queryFn: () => BaseApi.post("/tasks/submit-task/" + plugin.id + "/" + endpoint, body),
                staleTime: Infinity
            });
        });
    }, [pluginData, searchFormContext?.searchValues, queryClient]);

    if (pluginData.length === 0) {
        return <ErrorAlert title={"Database contains no catalogs"}
                           description={"Please contact the admins to add catalogs to the database."}/>
    }

    return (
        <>
            <h2 className="text-lg font-medium text-gray-900">Search results by sources</h2>
            <Tabs defaultValue={pluginData[0].id}>
                <TabsList>
                    {pluginData.map(plugin =>
                        <TabsTrigger key={`list_${plugin.id}`} value={plugin.id}>
                            {plugin.name}
                        </TabsTrigger>)}
                </TabsList>
                {pluginData.map(plugin =>
                    <TabsContent key={`content_${plugin.id}`} value={plugin.id}>
                        <StellarObjectsList plugin={plugin}/>
                    </TabsContent>)}
            </Tabs>
            <Button className="mt-2" disabled={identifiersContext?.lightCurveBtnDisabled} onClick={() => {
                setLightcurveSectionVisible(true);
                setCurrentObjectIdentifiers(identifiersContext?.selectedObjectIdentifiers ?? {});
            }}>
                Show photometric data
            </Button>

        </>
    )
}

export default StellarObjectsMenu;
