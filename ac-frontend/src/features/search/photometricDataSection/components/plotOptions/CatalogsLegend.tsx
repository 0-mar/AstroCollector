import {useContext, useEffect} from "react";
import {Database} from "lucide-react";
import { OptionsContext } from "./OptionsContext";
import {ColorsContext} from "@/features/search/photometricDataSection/components/plotOptions/ColorsContext.tsx";
import IconCheckbox from "@/features/search/photometricDataSection/components/plotOptions/IconCheckbox.tsx";

type CatalogsLegendProps = {
    pluginNames: Record<string, string>
}

const CatalogsLegend = ({pluginNames}: CatalogsLegendProps) => {
    const optionsContext = useContext(OptionsContext)
    const colorsContext = useContext(ColorsContext)

    useEffect(() => {
        const initial = Object.fromEntries(
            Object.entries(pluginNames).map(([id, name]) => [id, name])
        );
        optionsContext?.setSelectedPlugins(initial);
    }, [pluginNames]);

    return (
        <>
            <h3 className="text-lg text-gray-900">Filter by</h3>
            {Object.entries(pluginNames).map(([id, pluginName]) => {
                const isChecked = Boolean(optionsContext?.selectedPlugins[id])
                const onCheckedChange = (checked: boolean) => {
                    optionsContext?.setSelectedPlugins((prevSelected) => {
                        const updatedState = {...prevSelected}
                        if (checked) {
                            updatedState[id] = pluginName
                        } else {
                            delete updatedState[id]
                        }
                        return updatedState
                    })
                }
                return (
                    <IconCheckbox key={`${id}-checkbox`} checked={isChecked} id={`${id}-checkbox`} onCheckedChange={onCheckedChange} iconActive={<Database style={{color: `rgb(${colorsContext?.catalogColors[pluginName] ?? "0, 0, 0"})`}}/>} iconMuted={<Database className={"text-gray-600"}/>} label={pluginName} />
                )
            })}
        </>
    )
}

export default CatalogsLegend;
