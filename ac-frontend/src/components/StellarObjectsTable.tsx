import {useState} from "react";
import StellarObjectsCatalogList from "@/components/StellarObjectsCatalogList.tsx";
import LightcurveSection from "@/components/LightcurveSection.tsx";

export default function StellarObjectsTable({formData, pluginData}) {
    const [lightCurveBtnDisabled, setLightCurveBtnDisabled] = useState(true)
    const [selectedObjects, setSelectedObjects] = useState({})
    const [visible, setVisible] = useState(false)

    return (
        <>
            {pluginData.map(plugin => <StellarObjectsCatalogList key={plugin.id} formData={formData} plugin={plugin} setSelectedObjects={setSelectedObjects} setLightCurveBtnDisabled={setLightCurveBtnDisabled}></StellarObjectsCatalogList>)}
            <button disabled={lightCurveBtnDisabled} onClick={() => {setVisible(true)}}>Show light curve</button>
            {visible && <LightcurveSection selectedObjectIdentifiers={selectedObjects}></LightcurveSection>}
        </>
    )
}
