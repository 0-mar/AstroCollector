import {createFileRoute} from '@tanstack/react-router'
import {useState} from "react";
import SearchForm from "@/components/search/form/SearchForm.tsx";
import type {Identifiers} from "@/features/search/menu/types.ts";
import StellarObjectsMenu from '@/components/search/menu/StellarObjectsMenu';
import type {PluginDto, SearchValues} from "@/features/search/types.ts";
import LightCurveSection from "@/components/search/lightcurve/LightCurveSection.tsx";


export const Route = createFileRoute('/app/search')({
    component: TestComponent,
})


function TestComponent() {
    const [menuVisible, setMenuVisible] = useState(false)
    const [formData, setFormData] = useState<SearchValues>({})
    const [pluginData, setPluginData] = useState<PluginDto[]>([])


    const [currentObjectIdentifiers, setCurrentObjectIdentifiers] = useState<Identifiers>({})
    const [lightcurveSectionVisible, setLightcurveSectionVisible] = useState(false)

    return (
        // <div className="grid grid-cols-1 grid-rows-3 gap-4">
        <div>
            <div className="w-1/2 mx-auto">
                <SearchForm setMenuVisible={setMenuVisible} setFormData={setFormData} setPluginData={setPluginData}/>
            </div>
            <div>
                {menuVisible && <StellarObjectsMenu formData={formData} pluginData={pluginData}
                                                    setCurrentObjectIdentifiers={setCurrentObjectIdentifiers}
                                                    setLightcurveSectionVisible={setLightcurveSectionVisible}
                />}
            </div>
            <div>
                {lightcurveSectionVisible &&
                    <LightCurveSection currentObjectIdentifiers={currentObjectIdentifiers}/>}
            </div>
        </div>
    )
}
