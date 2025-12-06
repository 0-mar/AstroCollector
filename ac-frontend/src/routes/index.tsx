import {createFileRoute} from '@tanstack/react-router'
import {useEffect, useState} from "react";
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
    //const [aladinLoaded, setAladinLoaded] = useState(false)

    const [photometricSectionVisible, setPhotometricSectionVisible] = useState(false)

    const isAladinLoaded = useLoadAladin();

    /*useEffect(() => {
        const scriptTag = document.createElement('script')
        scriptTag.src = "https://aladin.cds.unistra.fr/AladinLite/api/v3/latest/aladin.js"
        scriptTag.addEventListener("load", () => {
           setAladinLoaded(true)
        })
        scriptTag.onload = () => {
            const A = (globalThis as any).A;
            // if aladin does not init within 10 seconds, fail
            const timeout = new Promise((_, rej) => setTimeout(() => rej(new Error('aladin-init-timeout')), 10000));
            Promise.race([A?.init ?? Promise.reject('no A'), timeout])
                .then(() => setAladinLoaded(true))
                .catch(() => setAladinLoaded(false)); // don't render Aladin
        };
        document.body.appendChild(scriptTag)
    }, []);*/

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
