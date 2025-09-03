import React, {createContext, useMemo, useState} from "react"

type RangeCtx = {
    currMinRange: number | undefined,
    currMaxRange: number | undefined
};

type SetRangeCtx = {
    setCurrMinRange: React.Dispatch<React.SetStateAction<number | undefined>>;
    setCurrMaxRange: React.Dispatch<React.SetStateAction<number | undefined>>;
}

export const RangeContext = createContext<RangeCtx | null>(null)
export const SetRangeContext = createContext<SetRangeCtx | null>(null)

export const RangeProvider = ({ children }) => {

    const [currMinRange, setCurrMinRange] = useState<number | undefined>(undefined)
    const [currMaxRange, setCurrMaxRange] = useState<number | undefined>(undefined)

    const setRangeCtx = useMemo(
        () => ({ setCurrMinRange, setCurrMaxRange }),
        []
    );

    const rangeCtx = useMemo(
        () => ({ currMinRange, currMaxRange }),
        [currMinRange, currMaxRange]
    );

    return (
        <RangeContext.Provider value={rangeCtx}>
            <SetRangeContext.Provider value={setRangeCtx}>
                {children}
            </SetRangeContext.Provider>
        </RangeContext.Provider>
    );
};
