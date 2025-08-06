import {createFileRoute} from '@tanstack/react-router'
import {useState} from "react";
import SearchForm from "@/components/search/form/SearchForm.tsx";
import type {Identifiers} from "@/features/search/menu/types.ts";
import StellarObjectsMenu from '@/components/search/menu/StellarObjectsMenu';
import type {PluginDto, SearchValues} from "@/features/search/types.ts";


export const Route = createFileRoute('/app/test')({
    component: TestComponent,
})


function TestComponent() {
    const [menuVisible, setMenuVisible] = useState(false)
    const [formData, setFormData] = useState<SearchValues>({})
    const [pluginData, setPluginData] = useState<PluginDto[]>([])

    const [lightCurveBtnDisabled, setLightCurveBtnDisabled] = useState(true)
    const [selectedObjectIdentifiers, setSelectedObjectIdentifiers] = useState<Identifiers>({})

    const [currentObjectIdentifiers, setCurrentObjectIdentifiers] = useState<Identifiers>({})
    const [lightcurveSectionVisible, setLightcurveSectionVisible] = useState(false)

    return (
        <div className="grid grid-cols-1 grid-rows-3 gap-4">
            <div className="w-1/2 mx-auto">
                <SearchForm setMenuVisible={setMenuVisible} setFormData={setFormData} setPluginData={setPluginData}/>
            </div>
            <div>
                {menuVisible && <StellarObjectsMenu formData={formData} pluginData={pluginData}
                                                    setCurrentObjectIdentifiers={setCurrentObjectIdentifiers}
                                                    selectedObjectIdentifiers={selectedObjectIdentifiers}
                                                    setSelectedObjectIdentifiers={setSelectedObjectIdentifiers}
                                                    lightCurveBtnDisabled={lightCurveBtnDisabled}
                                                    setLightCurveBtnDisabled={setLightCurveBtnDisabled}
                                                    setLightcurveSectionVisible={setLightcurveSectionVisible}
                />}
            </div>
            <div>
                {lightcurveSectionVisible &&
                    <p>Placeholder lightcurve</p>}
            </div>
        </div>
    )
}
