import React, {type JSX} from "react";
import {Label} from "@/../components/ui/label.tsx";

type IconCheckboxProps = React.ComponentProps<"input"> & {
    id: string
    checked: boolean,
    onCheckedChange: (checked: boolean) => void,
    iconActive: JSX.Element,
    iconMuted: JSX.Element,
    label: string,
}

const IconCheckbox = ({id, checked, onCheckedChange, iconActive, iconMuted, label}: IconCheckboxProps) => {
    return (
        <div className="flex items-start gap-3">
            <input type={'checkbox'} className={"sr-only"} aria-label={label} id={id} checked={checked} onChange={(e) => {onCheckedChange(e.target.checked)}}></input>
            <Label htmlFor={id}>{checked ? iconActive : iconMuted}{label}</Label>
        </div>
    )
}

export default IconCheckbox;
