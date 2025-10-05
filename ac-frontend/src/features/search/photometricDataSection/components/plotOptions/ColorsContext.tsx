import React, {createContext, useMemo} from "react"
import {COLORS} from "@/utils/color.ts";

type ColorsCtx = {
    catalogColors: Record<string, [number, number, number]>
    lightFilterColors: Record<string, [number, number, number]>
};

export const ColorsContext = createContext<ColorsCtx | null>(null)

type ColorsProviderProps = {
    currPluginNames: Record<string, string>,
    currLightFilters: Array<string>,
    children: React.ReactNode
}

export const ColorsProvider = ({ children, currPluginNames, currLightFilters }: ColorsProviderProps) => {
    // mapping of plugin name to visual color
    const catalogColors = useMemo(() => {
        const colorDict: Record<string, [number, number, number]> = {}
        Object.values(currPluginNames).forEach((pluginName, i) => {
            colorDict[pluginName] = COLORS[i % COLORS.length]
        })
        return colorDict
    }, [currPluginNames])

    // mapping of light filter to visual color
    const lightFilterColors = useMemo(() => {
        const colorDict: Record<string, [number, number, number]> = {}
        currLightFilters.forEach((lightFilter, i) => {
            colorDict[lightFilter] = COLORS[i % COLORS.length]
        })
        return colorDict
    }, [currLightFilters])

    return (
        <ColorsContext.Provider value={{catalogColors, lightFilterColors}}>
            {children}
        </ColorsContext.Provider>
    );
};
