import React, {createContext, useState} from "react"

type StellarObjectCoords = {
    rightAscension: number,
    declination: number
}

type ResolvedObjectCoordsCtx = {
    resolvedObjectCoords: StellarObjectCoords | null; setResolvedObjectCoords: React.Dispatch<React.SetStateAction<StellarObjectCoords | null>>
};

export const ResolvedObjectCoordsContext = createContext<ResolvedObjectCoordsCtx | null>(null)

export const ResolvedObjectCoordsProvider = ({ children }: { children: React.ReactNode }) => {
    const [resolvedObjectCoords, setResolvedObjectCoords] = useState<StellarObjectCoords | null>(null)

    return (
        <ResolvedObjectCoordsContext.Provider value={{resolvedObjectCoords, setResolvedObjectCoords}}>
            {children}
        </ResolvedObjectCoordsContext.Provider>
    );
};
