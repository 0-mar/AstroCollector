import React, {createContext, useMemo} from "react"
import {COLORS} from "@/utils/color.ts";

type ColorsCtx = {
    catalogColors: Record<string, [number, number, number]>
    bandpassFilterColors: Record<string, [number, number, number]>
};

export const ColorsContext = createContext<ColorsCtx | null>(null)

type ColorsProviderProps = {
    currPluginNames: Record<string, string>,
    currBandpassFilters: Array<string>,
    children: React.ReactNode
}

export const ColorsProvider = ({ children, currPluginNames, currBandpassFilters }: ColorsProviderProps) => {
    // mapping of plugin name to visual color
    const catalogColors = useMemo(() => {
        const colorDict: Record<string, [number, number, number]> = {}
        Object.values(currPluginNames).forEach((pluginName, i) => {
            colorDict[pluginName] = COLORS[i % COLORS.length]
        })
        return colorDict
    }, [currPluginNames])

    // mapping of bandpass filter to visual color
    const bandpassFilterColors = useMemo(() => {
        const colorDict: Record<string, [number, number, number]> = {}
        currBandpassFilters.forEach((bandpassFilter, i) => {
            colorDict[bandpassFilter] = COLORS[i % COLORS.length]
        })
        return colorDict
    }, [currBandpassFilters])

    return (
        <ColorsContext.Provider value={{catalogColors, bandpassFilterColors}}>
            {children}
        </ColorsContext.Provider>
    );
};
