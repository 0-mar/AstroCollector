import {useContext} from "react";
import { OptionsContext } from "./OptionsContext";
import { RadioGroup, RadioGroupItem } from "@/../components/ui/radio-group";
import { GroupOptions } from "./types";
import { Label } from "@radix-ui/react-label";
import CatalogsLegend from "@/features/search/photometricDataSection/components/plotOptions/CatalogsLegend.tsx";
import LightFiltersLegend from "@/features/search/photometricDataSection/components/plotOptions/LightFIltersLegend.tsx";
import ZoomForm from "@/features/search/photometricDataSection/components/plotOptions/ZoomForm.tsx";


type PlotOptionsPanelProps = {
    pluginNames: Record<string, string>
    lightFilters: string[]
}

const PlotOptionsPanel = ({pluginNames, lightFilters}: PlotOptionsPanelProps) => {
    const optionsContext = useContext(OptionsContext)

    return (
        <div className={"p-4 bg-white rounded-md shadow-md"}>
            <h2 className="text-xl font-medium text-gray-900">Options</h2>
            <div className={"grid grid-cols-3 gap-x-2"}>
                <section>
                    <h3 className="text-lg text-gray-900">Group by</h3>
                    <RadioGroup className={"mt-2"} value={optionsContext?.groupBy} onValueChange={(value: GroupOptions) => {optionsContext?.setGroupBy(value)}}>
                        <div className="flex items-center space-x-2">
                            <RadioGroupItem value={GroupOptions.CATALOGS} id={GroupOptions.CATALOGS} />
                            <Label htmlFor={GroupOptions.CATALOGS}>Catalogs (sources)</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                            <RadioGroupItem value={GroupOptions.BANDPASS_FILTERS} id={GroupOptions.BANDPASS_FILTERS} />
                            <Label htmlFor={GroupOptions.BANDPASS_FILTERS}>Photometric bandpass filters</Label>
                        </div>
                    </RadioGroup>
                </section>
                <section className={"flex flex-col gap-y-2 max-w-[200px] overflow-y-auto scrollbar-hide border-2 rounded-md p-2 border-gray-200"}>
                    {optionsContext?.groupBy === GroupOptions.CATALOGS ?
                        <CatalogsLegend pluginNames={pluginNames}/>
                        :
                        <LightFiltersLegend lightFilters={lightFilters}/>
                    }

                </section>
                <div>
                    <ZoomForm/>
                </div>
            </div>
        </div>
    );
}

export default PlotOptionsPanel;
