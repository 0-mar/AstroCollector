import {createFileRoute} from '@tanstack/react-router'
import {useEffect, useState} from "react";
import SearchForm from "@/features/search/searchSection/components/SearchForm.tsx";
import StellarObjectsMenu from "@/features/search/menuSection/components/StellarObjectsMenu.tsx";
import PhotometricDataSection from "@/features/search/photometricDataSection/components/PhotometricDataSection.tsx";
import {IdentifiersProvider} from "@/features/search/menuSection/components/IdentifiersContext.tsx";
import {SearchFormProvider} from "@/features/search/searchSection/components/SearchFormContext.tsx";
import {ObjectCoordsProvider} from "@/features/search/searchSection/components/ObjectCoordsProvider.tsx";
import AladinCutout from "@/features/search/searchSection/components/AladinCutout.tsx";
import type {PluginDto} from "@/features/plugin/types.ts";

export const Route = createFileRoute('/')({
    component: App,
})

function App() {
    const [menuVisible, setMenuVisible] = useState(false)
    const [pluginData, setPluginData] = useState<PluginDto[]>([])
    const [aladinLoaded, setAladinLoaded] = useState(false)

    const [photometricSectionVisible, setPhotometricSectionVisible] = useState(false)

    useEffect(() => {
        const scriptTag = document.createElement('script')
        scriptTag.src = "https://aladin.cds.unistra.fr/AladinLite/api/v3/latest/aladin.js"
        scriptTag.addEventListener("load", () => {
           setAladinLoaded(true)
        })
        document.body.appendChild(scriptTag)
    }, []);

    return (
        <SearchFormProvider>
            <ObjectCoordsProvider>
                <IdentifiersProvider>
                    <div className="flex flex-wrap bg-blue-100">
                        <div className="p-8 w-full md:w-1/2 min-w-0">
                            <SearchForm setMenuVisible={setMenuVisible}
                                        setLightcurveSectionVisible={setPhotometricSectionVisible}
                                        setPluginData={setPluginData}/>
                        </div>
                        {menuVisible && <div className="p-8 w-full md:w-1/2 min-w-0">
                            <AladinCutout loaded={aladinLoaded} />
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
            </ObjectCoordsProvider>
        </SearchFormProvider>
    )
}
