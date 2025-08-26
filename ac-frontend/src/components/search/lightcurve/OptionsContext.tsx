import React, {createContext, useMemo, useState} from "react"

type OptionsCtx = {
    showErrorBars: boolean; setShowErrorBars: React.Dispatch<React.SetStateAction<boolean>>;
    groupBy: string; setGroupBy: React.Dispatch<React.SetStateAction<string>>;
    minRange: number | undefined; setMinRange: React.Dispatch<React.SetStateAction<number | undefined>>;
    maxRange: number | undefined; setMaxRange: React.Dispatch<React.SetStateAction<number | undefined>>;
};

export const OptionsContext = createContext<OptionsCtx | null>(null)

export const OptionsProvider = ({ children }) => {
    const [showErrorBars, setShowErrorBars] = useState(false)
    const [groupBy, setGroupBy] = useState("sources")
    const [minRange, setMinRange] = useState<number | undefined>(undefined)
    const [maxRange, setMaxRange] = useState<number | undefined>(undefined)

    const value = useMemo(
        () => ({
            showErrorBars,
            setShowErrorBars,
            groupBy,
            setGroupBy,
            minRange,
            setMinRange,
            maxRange,
            setMaxRange,
        }),
        [showErrorBars, groupBy, minRange, maxRange]
    );

    return (
        <OptionsContext.Provider value={value}>
            {children}
        </OptionsContext.Provider>
    );
};
