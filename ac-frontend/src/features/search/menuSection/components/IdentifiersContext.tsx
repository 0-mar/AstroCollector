import React, {createContext, useMemo, useState} from "react"
import type {Identifiers} from "@/features/search/menuSection/types.ts";

type IdentifiersCtx = {
    selectedObjectIdentifiers: Identifiers; setSelectedObjectIdentifiers: React.Dispatch<React.SetStateAction<Identifiers>>;
    lightCurveBtnDisabled: boolean; setLightCurveBtnDisabled: React.Dispatch<React.SetStateAction<boolean>>;
};

export const IdentifiersContext = createContext<IdentifiersCtx | null>(null)

export const IdentifiersProvider = ({ children }: {children: React.ReactNode}) => {
    const [selectedObjectIdentifiers, setSelectedObjectIdentifiers] = useState<Identifiers>({})
    const [lightCurveBtnDisabled, setLightCurveBtnDisabled] = useState(true)

    const value = useMemo(
        () => ({
            selectedObjectIdentifiers,
            setSelectedObjectIdentifiers,
            lightCurveBtnDisabled,
            setLightCurveBtnDisabled,
        }),
        [selectedObjectIdentifiers, lightCurveBtnDisabled]
    );

    return (
        <IdentifiersContext.Provider value={value}>
            {children}
        </IdentifiersContext.Provider>
    );
};
