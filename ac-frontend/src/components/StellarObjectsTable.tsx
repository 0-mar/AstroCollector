import '../styles.css'
import StellarObjectsCatalogList from "@/components/StellarObjectsCatalogList.tsx";
import {useState} from "react";

export default function StellarObjectsTable({formData, pluginData}) {
    const [lightCurveBtnDisabled, setLightCurveBtnDisabled] = useState(true)
    const [selectedObjects, setSelectedObjects] = useState({})

    return (
        <>
            {pluginData.map(plugin => <StellarObjectsCatalogList key={plugin.id} formData={formData} plugin={plugin} setSelectedObjects={setSelectedObjects} setLightCurveBtnDisabled={setLightCurveBtnDisabled}></StellarObjectsCatalogList>)}
            <button disabled={lightCurveBtnDisabled} onClick={() => {console.log("Show lightcurve: " + selectedObjects)}}>Show light curve</button>
        </>
    )
}
