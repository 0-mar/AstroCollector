import {createFileRoute} from '@tanstack/react-router'
import {useState} from "react";
import type {PluginDto} from "@/features/search/types.ts";
import type {Identifiers} from "@/features/search/menu/types.ts";
import SearchForm from "@/components/search/form/SearchForm.tsx";
import StellarObjectsMenu from "@/components/search/menu/StellarObjectsMenu.tsx";
import PhotometricDataSection from "@/components/search/photometricData/PhotometricDataSection.tsx";
import {IdentifiersProvider} from "@/components/search/menu/IdentifiersContext.tsx";
import {SearchFormProvider} from "@/components/search/form/SearchFormContext.tsx";
import {ObjectCoordsProvider} from "@/components/search/form/ObjectCoordsProvider.tsx";

export const Route = createFileRoute('/')({
    component: App,
})

function App() {
    const [menuVisible, setMenuVisible] = useState(false)
    const [pluginData, setPluginData] = useState<PluginDto[]>([])


    const [currentObjectIdentifiers, setCurrentObjectIdentifiers] = useState<Identifiers>({})
    const [lightcurveSectionVisible, setLightcurveSectionVisible] = useState(false)

    return (
        //<div className="grid grid-cols-1 grid-rows-3 gap-4">
        <div>
            <SearchFormProvider>
                <ObjectCoordsProvider>
                    <IdentifiersProvider>
                        <div className="bg-blue-100 rounded-md">
                            <div className="p-8 w-1/2 0mx-auto">
                                <SearchForm setMenuVisible={setMenuVisible}
                                            setCurrentObjectIdentifiers={setCurrentObjectIdentifiers}
                                            setLightcurveSectionVisible={setLightcurveSectionVisible}
                                            setPluginData={setPluginData}/>
                            </div>

                        </div>
                        {menuVisible && <div className="p-8 my-4">
                            <StellarObjectsMenu pluginData={pluginData}
                                                setCurrentObjectIdentifiers={setCurrentObjectIdentifiers}
                                                setLightcurveSectionVisible={setLightcurveSectionVisible}
                            />
                        </div>}
                        {lightcurveSectionVisible && <div className="bg-blue-100 rounded-md">
                            <div className={"p-8"}>
                                <PhotometricDataSection currentObjectIdentifiers={currentObjectIdentifiers}
                                                        pluginData={pluginData}/>
                            </div>
                        </div>}
                    </IdentifiersProvider>
                </ObjectCoordsProvider>
            </SearchFormProvider>
        </div>
    )
}
