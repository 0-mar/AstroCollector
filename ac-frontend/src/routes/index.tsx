import {createFileRoute} from '@tanstack/react-router'
import {useState} from "react";
import SearchForm from "@/features/search/searchSection/components/SearchForm.tsx";
import StellarObjectsMenu from "@/features/search/menuSection/components/StellarObjectsMenu.tsx";
import PhotometricDataSection from "@/features/search/photometricDataSection/components/PhotometricDataSection.tsx";
import {IdentifiersProvider} from "@/features/search/menuSection/components/IdentifiersContext.tsx";
import {SearchFormProvider} from "@/features/search/searchSection/components/SearchFormContext.tsx";
import {ResolvedObjectCoordsProvider} from "@/features/search/searchSection/components/ResolvedObjectCoordsProvider.tsx";
import AladinCutout from "@/features/search/searchSection/components/AladinCutout.tsx";
import type {PluginDto} from "@/features/catalogsOverview/types.ts";
import {useLoadAladin} from "@/features/search/searchSection/hooks/useLoadAladin.ts";

export const Route = createFileRoute('/')({
    component: App,
})

function App() {
    const [menuVisible, setMenuVisible] = useState(false)
    const [pluginData, setPluginData] = useState<PluginDto[]>([])

    const [photometricSectionVisible, setPhotometricSectionVisible] = useState(false)

    const isAladinLoaded = useLoadAladin();

    return (
        <SearchFormProvider>
            <ResolvedObjectCoordsProvider>
                <IdentifiersProvider>
                    <div className="flex flex-wrap bg-blue-100">
                        <div className="p-8 w-full md:w-1/2 min-w-0">
                            <SearchForm setMenuVisible={setMenuVisible}
                                        setLightcurveSectionVisible={setPhotometricSectionVisible}
                                        setPluginData={setPluginData}/>
                        </div>
                        {menuVisible && <div className="p-8 w-full md:w-1/2 min-w-0">
                            <AladinCutout loaded={isAladinLoaded} />
                        </div>}
                    </div>
                    {menuVisible && <div className="p-8 my-4">
                        <StellarObjectsMenu pluginData={pluginData}
                                            setLightcurveSectionVisible={setPhotometricSectionVisible}
                        />
                    </div>}
                    {photometricSectionVisible && <div className="bg-blue-100 rounded-md">
                        <div className={"p-8"}>
                            <PhotometricDataSection pluginData={pluginData}/>
                        </div>
                    </div>}
                </IdentifiersProvider>
            </ResolvedObjectCoordsProvider>
        </SearchFormProvider>
    )
}
