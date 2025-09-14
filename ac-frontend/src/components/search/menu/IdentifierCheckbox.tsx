import {Checkbox} from "@/../components/ui/checkbox"
import {useContext, useEffect, useState} from "react";
import {IdentifiersContext} from "@/components/search/menu/IdentifiersContext.tsx";
import type {Identifiers} from "@/features/search/menu/types.ts";
import type {StellarObjectIdentifierDto} from "@/features/search/types.ts";

type IdentifierCheckboxProps = {
    id: string,
    identifier: StellarObjectIdentifierDto,
};

export const IdentifierCheckbox = ({
                                       id,
                                       identifier,
                                   }: IdentifierCheckboxProps) => {
    const identifiersContext = useContext(IdentifiersContext)
    const [checked, setChecked] = useState(identifiersContext?.selectedObjectIdentifiers[id] === identifier);

    useEffect(() => {
        setChecked(identifiersContext?.selectedObjectIdentifiers[id] === identifier)
    }, [identifiersContext?.selectedObjectIdentifiers[id]]);

    const handleCheckedChange = (isChecked: boolean) => {
        setChecked(isChecked)
        identifiersContext?.setSelectedObjectIdentifiers((prevState) => {
            const updatedState: Identifiers = {...prevState}
            if (isChecked) {
                updatedState[id] = identifier
            } else {
                delete updatedState[id]
            }
            identifiersContext?.setLightCurveBtnDisabled(Object.keys(updatedState).length === 0)

            return updatedState
        })
    }

    return (
        <Checkbox
            id={id}
            checked={checked}
            onCheckedChange={handleCheckedChange}
        />
    )
}

export default IdentifierCheckbox;
