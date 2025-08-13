import {createFileRoute} from '@tanstack/react-router'
import {useState} from "react";
import type {PluginDto, SearchValues} from "@/features/search/types.ts";
import type {Identifiers} from "@/features/search/menu/types.ts";
import SearchForm from "@/components/search/form/SearchForm.tsx";
import StellarObjectsMenu from "@/components/search/menu/StellarObjectsMenu.tsx";
import LightCurveSection from "@/components/search/lightcurve/LightCurveSection.tsx";

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
            <div className="w-1/2 0mx-auto">
                <SearchForm setMenuVisible={setMenuVisible} setFormData={setFormData} setPluginData={setPluginData}/>
            </div>
            <div className="my-6">
                {menuVisible && <StellarObjectsMenu formData={formData} pluginData={pluginData}
                                                    setCurrentObjectIdentifiers={setCurrentObjectIdentifiers}
                                                    setLightcurveSectionVisible={setLightcurveSectionVisible}
                />}
            </div>
            <div>
                {lightcurveSectionVisible &&
                    <LightCurveSection currentObjectIdentifiers={currentObjectIdentifiers} pluginData={pluginData}/>}
            </div>
        </div>
    )
}
