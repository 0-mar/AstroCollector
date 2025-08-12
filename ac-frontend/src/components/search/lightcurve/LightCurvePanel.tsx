import {Checkbox} from "@/../components/ui/checkbox"
import { Label } from "@/../components/ui/label"
import * as React from "react";

type LightCurvePanelProps = {
    showErrorBars: boolean,
    setShowErrorBars: React.Dispatch<React.SetStateAction<boolean>>
}

const LightCurvePanel = ({showErrorBars, setShowErrorBars}: LightCurvePanelProps) => {
    return (
        <div>
            <h2>Options</h2>
            <div className={"flex"}>
                <Checkbox id={"errorBars"} checked={showErrorBars} onCheckedChange={(checked) => setShowErrorBars(checked)}></Checkbox>
                <Label htmlFor="errorBars">Show error bars</Label>
            </div>
        </div>
    );
}

export default LightCurvePanel;
