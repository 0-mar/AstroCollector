import type {PluginDto, SearchValues} from "@/features/search/types.ts";
import * as React from "react";
import type {Identifiers} from "@/features/search/menu/types.ts";
import {Tabs, TabsContent, TabsList, TabsTrigger} from "@/../components/ui/tabs"
import StellarObjectsList from "@/components/search/menu/StellarObjectsList.tsx";
import {Button} from "@/../components/ui/button"
import LoadingError from "@/components/loading/LoadingError.tsx";
import {useEffect, useState} from "react";
import {useQueryClient} from "@tanstack/react-query";
import BaseApi from "@/features/api/baseApi.ts";

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

    const [selectedObjectIdentifiers, setSelectedObjectIdentifiers] = useState<Identifiers>({})
    const [lightCurveBtnDisabled, setLightCurveBtnDisabled] = useState(true)

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
        return <LoadingError title={"Database contains no catalogs"}
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
                        <StellarObjectsList formData={formData} plugin={plugin}
                                            selectedObjectIdentifiers={selectedObjectIdentifiers}
                                            setSelectedObjectIdentifiers={setSelectedObjectIdentifiers}
                                            setLightCurveBtnDisabled={setLightCurveBtnDisabled}/>
                    </TabsContent>)}
            </Tabs>
            <Button disabled={lightCurveBtnDisabled} onClick={() => {
                setLightcurveSectionVisible(true);
                setCurrentObjectIdentifiers(selectedObjectIdentifiers);
            }}>
                Show light curve
            </Button>

        </>
    )
}

export default StellarObjectsMenu;
