import type {PluginDto, SearchValues} from "@/features/search/types.ts";
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

type StellarObjectsMenuProps = {
    formData: SearchValues
    pluginData: PluginDto[]
    setLightcurveSectionVisible: React.Dispatch<React.SetStateAction<boolean>>
    setCurrentObjectIdentifiers: React.Dispatch<React.SetStateAction<Identifiers>>
};

const StellarObjectsMenu = ({
                                formData,
                                pluginData,
                                setLightcurveSectionVisible,
                                setCurrentObjectIdentifiers
                            }: StellarObjectsMenuProps) => {

    const identifiersContext = useContext(IdentifiersContext);

    const queryClient = useQueryClient();
    useEffect(() => {
        pluginData.forEach(plugin => {
            console.log("Prefetching plugin", plugin.id);
            const body = formData.objectName !== "" ?
                {name: formData.objectName, plugin_id: plugin.id} :
                {
                    right_ascension_deg: formData.rightAscension,
                    declination_deg: formData.declination,
                    radius: formData.radius,
                    plugin_id: plugin.id
                };

            const endpoint = formData.objectName !== "" ? "find-object" : "cone-search";

            // Prefetch Submit Task (same as taskQuery)
            queryClient.prefetchQuery({
                queryKey: [`plugin_${plugin.id}`, formData],
                queryFn: () => BaseApi.post("/tasks/submit-task/" + plugin.id + "/" + endpoint, body),
                staleTime: Infinity
            });
        });
    }, [pluginData, formData, queryClient]);

    if (pluginData.length === 0) {
        return <ErrorAlert title={"Database contains no catalogs"}
                           description={"Please contact the admins to add catalogs to the database."}/>
    }

    return (
        <>
            <Tabs defaultValue={pluginData[0].id}>
                <TabsList>
                    {pluginData.map(plugin =>
                        <TabsTrigger key={`list_${plugin.id}`} value={plugin.id}>
                            {plugin.name}
                        </TabsTrigger>)}
                </TabsList>
                {pluginData.map(plugin =>
                    <TabsContent key={`content_${plugin.id}`} value={plugin.id}>
                        <StellarObjectsList formData={formData} plugin={plugin}/>
                    </TabsContent>)}
            </Tabs>
            <Button className="mt-2" disabled={identifiersContext?.lightCurveBtnDisabled} onClick={() => {
                setLightcurveSectionVisible(true);
                setCurrentObjectIdentifiers(identifiersContext?.selectedObjectIdentifiers ?? {});
            }}>
                Show light curve
            </Button>

        </>
    )
}

export default StellarObjectsMenu;
