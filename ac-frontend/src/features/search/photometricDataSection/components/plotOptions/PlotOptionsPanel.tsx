import {Checkbox} from "../../../../../../components/ui/checkbox.tsx"
import { Label } from "../../../../../../components/ui/label.tsx"
import {RadioGroup, RadioGroupItem} from "../../../../../../components/ui/radio-group.tsx";
import ZoomForm from "@/features/search/photometricDataSection/components/plotOptions/ZoomForm.tsx";
import {useContext} from "react";
import {OptionsContext} from "@/features/search/photometricDataSection/components/plotOptions/OptionsContext.tsx";


const PlotOptionsPanel = () => {
    const context = useContext(OptionsContext)

    return (
        <div className={"p-4 bg-white rounded-md shadow-md"}>
            <h2>Options</h2>
            <div className={"grid grid-cols-2 gap-x-2"}>
                <div>
                    <h3>Error bars</h3>
                    <div className={"flex mt-2 mb-2 items-center space-x-2"}>
                        <Checkbox id={"errorBars"} checked={context?.showErrorBars} onCheckedChange={(checked) => context?.setShowErrorBars(checked)}></Checkbox>
                        <Label htmlFor="errorBars">Show error bars</Label>
                    </div>
                </div>
                <div>
                    <h3>Group by</h3>
                    <RadioGroup className={"mt-2"} defaultValue={context?.groupBy} onValueChange={(value) => {context?.setGroupBy(value)}}>
                        <div className="flex items-center space-x-2">
                            <RadioGroupItem value="sources" id="sources" />
                            <Label htmlFor="sources">Sources (catalogs)</Label>
                        </div>
                        <div className="flex items-center space-x-2">
                            <RadioGroupItem value="bands" id="bands" />
                            <Label htmlFor="bands">Photometric bands</Label>
                        </div>
                    </RadioGroup>
                </div>
                <div>
                    <ZoomForm/>
                </div>
            </div>
        </div>
    );
}

export default PlotOptionsPanel;
