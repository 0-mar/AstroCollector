import React, {createContext, useMemo, useState} from "react"

type ObjectCoords = {
    rightAscension: number | undefined,
    declination: number | undefined
}

type ObjectCoordsCtx = {
    objectCoords: ObjectCoords; setObjectCoords: React.Dispatch<React.SetStateAction<ObjectCoords>>;
};

export const ObjectCoordsContext = createContext<ObjectCoordsCtx | null>(null)

export const ObjectCoordsProvider = ({ children }) => {
    const [objectCoords, setObjectCoords] = useState<ObjectCoords>({declination: undefined, rightAscension: undefined})

    const value = useMemo(
        () => ({
            objectCoords,
            setObjectCoords,
        }),
        [objectCoords]
    );

    return (
        <ObjectCoordsContext.Provider value={value}>
            {children}
        </ObjectCoordsContext.Provider>
    );
};
