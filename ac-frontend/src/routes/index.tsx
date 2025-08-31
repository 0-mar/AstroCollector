import {createFileRoute} from '@tanstack/react-router'
import {useState} from "react";
import type {PluginDto, SearchValues} from "@/features/search/types.ts";
import type {Identifiers} from "@/features/search/menu/types.ts";
import SearchForm from "@/components/search/form/SearchForm.tsx";
import StellarObjectsMenu from "@/components/search/menu/StellarObjectsMenu.tsx";
import LightCurveSection from "@/components/search/lightcurve/LightCurveSection.tsx";
import {IdentifiersProvider} from "@/components/search/menu/IdentifiersContext.tsx";

export const Route = createFileRoute('/')({
    component: App,
})

function App() {
    const [menuVisible, setMenuVisible] = useState(false)
    const [formData, setFormData] = useState<SearchValues>({})
    const [pluginData, setPluginData] = useState<PluginDto[]>([])


    const [currentObjectIdentifiers, setCurrentObjectIdentifiers] = useState<Identifiers>({})
    const [lightcurveSectionVisible, setLightcurveSectionVisible] = useState(false)

    return (
        //<div className="grid grid-cols-1 grid-rows-3 gap-4">
        <div>
            <div className="bg-blue-100 rounded-md">
                <div className="p-8 w-1/2 0mx-auto">
                    <SearchForm setMenuVisible={setMenuVisible} setFormData={setFormData} setPluginData={setPluginData}/>
                </div>

            </div>
            {menuVisible && <div className="p-8 my-4">
                <IdentifiersProvider><StellarObjectsMenu formData={formData} pluginData={pluginData}
                                                    setCurrentObjectIdentifiers={setCurrentObjectIdentifiers}
                                                    setLightcurveSectionVisible={setLightcurveSectionVisible}
                /></IdentifiersProvider>
            </div>}
            {lightcurveSectionVisible && <div className="bg-blue-100 rounded-md">
                <div className={"p-8"}>
                    <LightCurveSection currentObjectIdentifiers={currentObjectIdentifiers} pluginData={pluginData}/>
                </div>
            </div>}
        </div>
    )
}
