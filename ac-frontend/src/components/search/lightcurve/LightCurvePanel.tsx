import {Checkbox} from "@/../components/ui/checkbox"
import { Label } from "@/../components/ui/label"
import * as React from "react";
import {RadioGroup, RadioGroupItem} from "@/../components/ui/radio-group";

type LightCurvePanelProps = {
    showErrorBars: boolean,
    setShowErrorBars: React.Dispatch<React.SetStateAction<boolean>>,
    groupBy: string,
    setGroupBy: React.Dispatch<React.SetStateAction<string>>,
}

const LightCurvePanel = ({showErrorBars, setShowErrorBars, groupBy, setGroupBy}: LightCurvePanelProps) => {
    return (
        <div>
            <h2>Options</h2>
            <div className={"flex"}>
                <Checkbox id={"errorBars"} checked={showErrorBars} onCheckedChange={(checked) => setShowErrorBars(checked)}></Checkbox>
                <Label htmlFor="errorBars">Show error bars</Label>
            </div>
            <h3>Group by</h3>
            <RadioGroup defaultValue={groupBy} onValueChange={(value) => {setGroupBy(value)}}>
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
    );
}

export default LightCurvePanel;
