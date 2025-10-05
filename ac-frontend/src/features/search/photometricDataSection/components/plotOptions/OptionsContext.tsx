import React, {createContext, useMemo, useState} from "react"
import {GroupOptions} from "@/features/search/photometricDataSection/components/plotOptions/types.ts";

export type ZoomCords = {
    xMin: number,
    xMax: number,
    yMin: number,
    yMax: number,
}

type OptionsCtx = {
    groupBy: GroupOptions; setGroupBy: React.Dispatch<React.SetStateAction<GroupOptions>>;
    selectedPlugins: Record<string, string>; setSelectedPlugins: React.Dispatch<React.SetStateAction<Record<string, string>>>;
    selectedBandpassFilters: Set<string>, setSelectedBandpassFilters: React.Dispatch<React.SetStateAction<Set<string>>>;
    zoomToCoords: ZoomCords | null; setZoomToCoords: React.Dispatch<React.SetStateAction<ZoomCords | null>>;
};

export const OptionsContext = createContext<OptionsCtx | null>(null)

export const OptionsProvider = ({ children }: {children: React.ReactNode}) => {
    const [groupBy, setGroupBy] = useState(GroupOptions.CATALOGS)
    const [selectedPlugins, setSelectedPlugins] = useState<Record<string, string>>({})
    const [selectedBandpassFilters, setSelectedBandpassFilters] = useState<Set<string>>(new Set<string>())
    const [zoomToCoords, setZoomToCoords] = useState(null)

    const value = useMemo(
        () => ({
            groupBy,
            setGroupBy,
            selectedPlugins,
            setSelectedPlugins,
            selectedBandpassFilters,
            setSelectedBandpassFilters,
            zoomToCoords,
            setZoomToCoords
        }),
        [groupBy, selectedPlugins, selectedBandpassFilters, zoomToCoords]
    );

    return (
        <OptionsContext.Provider value={value}>
            {children}
        </OptionsContext.Provider>
    );
};
