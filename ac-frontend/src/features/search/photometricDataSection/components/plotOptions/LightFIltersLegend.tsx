import {useContext, useEffect} from "react";
import {Database} from "lucide-react";
import {OptionsContext} from "@/features/search/photometricDataSection/components/plotOptions/OptionsContext.tsx";
import {ColorsContext} from "@/features/search/photometricDataSection/components/plotOptions/ColorsContext.tsx";
import IconCheckbox from "@/features/search/photometricDataSection/components/plotOptions/IconCheckbox.tsx";

type LightFiltersLegendProps = {
    lightFilters: string[]
}

const LightFiltersLegend = ({lightFilters}: LightFiltersLegendProps) => {
    const optionsContext = useContext(OptionsContext)
    const colorsContext = useContext(ColorsContext)

    // show all traces in the beginning
    useEffect(() => {
        optionsContext?.setSelectedBandpassFilters(new Set<string>(lightFilters));
    }, [lightFilters]);

    return (
        <>
            <h3 className="text-lg text-gray-900">Filter by</h3>
            {lightFilters.map((filter) => {
                const isChecked = Boolean(optionsContext?.selectedBandpassFilters.has(filter))
                const onCheckedChange = (checked: boolean) => {
                    optionsContext?.setSelectedBandpassFilters((prevSelected) => {
                        const updatedState = new Set<string>(prevSelected.values())
                        if (checked) {
                            updatedState.add(filter)
                        } else {
                            updatedState.delete(filter)
                        }
                        return updatedState
                    })
                }
                return (
                    <IconCheckbox key={`${filter}-checkbox`} checked={isChecked} id={`${filter}-checkbox`} onCheckedChange={onCheckedChange} iconActive={<Database style={{color: `rgb(${colorsContext?.bandpassFilterColors[filter] ?? "0, 0, 0"})`}}/>} iconMuted={<Database className={"text-gray-600"}/>} label={filter} />
                )
            })}
        </>
    )
}

export default LightFiltersLegend;
