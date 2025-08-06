import type {PluginDto, SearchValues} from "@/features/search/types.ts";
import * as React from "react";
import type {Identifiers} from "@/features/search/menu/types.ts";
import {Tabs, TabsContent, TabsList, TabsTrigger} from "@/../components/ui/tabs"
import StellarObjectsList from "@/components/search/menu/StellarObjectsList.tsx";
import {Button} from "@/../components/ui/button"
import LoadingError from "@/components/loading/LoadingError.tsx";

type StellarObjectsMenuProps = {
    formData: SearchValues
    pluginData: PluginDto[]
    lightCurveBtnDisabled: boolean
    setLightCurveBtnDisabled: React.Dispatch<React.SetStateAction<boolean>>
    selectedObjectIdentifiers: Identifiers
    setSelectedObjectIdentifiers: React.Dispatch<React.SetStateAction<Identifiers>>
    setLightcurveSectionVisible: React.Dispatch<React.SetStateAction<boolean>>
    setCurrentObjectIdentifiers: React.Dispatch<React.SetStateAction<Identifiers>>
};

const StellarObjectsMenu = ({
                                formData,
                                pluginData,
                                lightCurveBtnDisabled,
                                setLightCurveBtnDisabled,
                                selectedObjectIdentifiers,
                                setSelectedObjectIdentifiers,
                                setLightcurveSectionVisible,
                                setCurrentObjectIdentifiers
                            }: StellarObjectsMenuProps) => {
    if (pluginData.length === 0) {
        return <LoadingError title={"Database contains no catalogs"}
                             description={"Please contact the admins to add catalogs to the database."}/>
    }

    return (
        <div>
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

        </div>
    )
}

export default StellarObjectsMenu;
