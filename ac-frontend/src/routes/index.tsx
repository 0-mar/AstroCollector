import {createFileRoute} from '@tanstack/react-router'
import {useEffect, useState} from "react";
import type {PluginDto} from "@/features/search/types.ts";
import SearchForm from "@/components/search/form/SearchForm.tsx";
import StellarObjectsMenu from "@/components/search/menu/StellarObjectsMenu.tsx";
import PhotometricDataSection from "@/components/search/photometricData/PhotometricDataSection.tsx";
import {IdentifiersProvider} from "@/components/search/menu/IdentifiersContext.tsx";
import {SearchFormProvider} from "@/components/search/form/SearchFormContext.tsx";
import {ObjectCoordsProvider} from "@/components/search/form/ObjectCoordsProvider.tsx";
import AladinCutout from "@/components/search/form/AladinCutout.tsx";

export const Route = createFileRoute('/')({
    component: App,
})

function App() {
    const [menuVisible, setMenuVisible] = useState(false)
    const [pluginData, setPluginData] = useState<PluginDto[]>([])
    const [aladinLoaded, setAladinLoaded] = useState(false)

    const [lightcurveSectionVisible, setLightcurveSectionVisible] = useState(false)

    useEffect(() => {
        const scriptTag = document.createElement('script')
        scriptTag.src = "https://aladin.cds.unistra.fr/AladinLite/api/v3/latest/aladin.js"
        scriptTag.addEventListener("load", () => {
           setAladinLoaded(true)
        })
        document.body.appendChild(scriptTag)
    }, []);

    return (
        //<div className="grid grid-cols-1 grid-rows-3 gap-4">
        <div className={"h-full bg-blue-400"}>
            <SearchFormProvider>
                <ObjectCoordsProvider>
                    <IdentifiersProvider>
                        <div className="flex flex-wrap bg-blue-100">
                            <div className="p-8 w-full md:w-1/2 min-w-0">
                                <SearchForm setMenuVisible={setMenuVisible}
                                            setLightcurveSectionVisible={setLightcurveSectionVisible}
                                            setPluginData={setPluginData}/>
                            </div>
                            {menuVisible && <div className="p-8 w-full md:w-1/2 min-w-0">
                                <AladinCutout loaded={aladinLoaded} />
                            </div>}
                        </div>
                        {menuVisible && <div className="p-8 my-4">
                            <StellarObjectsMenu pluginData={pluginData}
                                                setLightcurveSectionVisible={setLightcurveSectionVisible}
                            />
                        </div>}
                        {lightcurveSectionVisible && <div className="bg-blue-100 rounded-md">
                            <div className={"p-8"}>
                                <PhotometricDataSection pluginData={pluginData}/>
                            </div>
                        </div>}
                    </IdentifiersProvider>
                </ObjectCoordsProvider>
            </SearchFormProvider>
        </div>
    )
}
