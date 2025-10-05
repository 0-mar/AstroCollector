import {useCallback, useContext} from "react";
import type { PhotometricDataDto } from "../../types.ts";
import {OptionsContext} from "../plotOptions/OptionsContext.tsx";
import {ColorsContext} from "@/features/search/photometricDataSection/components/plotOptions/ColorsContext.tsx";
import { unknownBandpassFilter } from "../PhotometricDataSection.tsx";
import ScatterPlotDeckGl from "@/features/search/photometricDataSection/components/scatterPlot/ScatterPlotDeckGl.tsx";
import {GroupOptions} from "@/features/search/photometricDataSection/components/plotOptions/types.ts";


type LightCurveGlPlotProps = {
    data: PhotometricDataDto[],
    pluginNames: Record<string, string>
}

const LightCurveGlPlot = ({data, pluginNames}: LightCurveGlPlotProps) => {
    const optionsContext = useContext(OptionsContext);
    const colorContext = useContext(ColorsContext)

    const filterByCatalog = useCallback((dto: PhotometricDataDto) => dto.plugin_id, [])
    const filterByBandpassFilter = useCallback((dto: PhotometricDataDto) => dto.light_filter ?? unknownBandpassFilter, [])

    const getCatalogColor = useCallback((dto: PhotometricDataDto) => {
        return colorContext?.catalogColors[pluginNames[dto.plugin_id]] ?? [0, 0, 0]
    }, [colorContext?.catalogColors])

    const getBandpassFilterColor = useCallback((dto: PhotometricDataDto) => {
        return colorContext?.bandpassFilterColors[dto.light_filter ?? unknownBandpassFilter] ?? [0, 0, 0]
    }, [colorContext?.bandpassFilterColors])

    const xDataFn = useCallback((dto: PhotometricDataDto) => {
        return dto.julian_date - 2400000
    }, [])

    const tooltipFn = useCallback((dto: PhotometricDataDto | null) => {
        return (dto ? {
            text: `JD: ${xDataFn(dto).toFixed(3)}\nMag: ${dto.magnitude.toFixed(2)}\nMag Err: ${dto.magnitude_error.toFixed(3)}\nFilter: ${dto.light_filter ?? unknownBandpassFilter}\nCatalog: ${pluginNames[dto.plugin_id]}`
        } : null)}
        , [pluginNames])

    return (
        <div className="bg-white shadow-md rounded-md min-h-[520px] w-full">
            <ScatterPlotDeckGl data={data}
                               xTitle={'Julian Date - 2400000 in TDB'}
                               yTitle={'Magnitude'}
                               colorFn={optionsContext?.groupBy === GroupOptions.CATALOGS ? getCatalogColor : getBandpassFilterColor}
                               xDataFn={xDataFn}
                               tooltipFn={tooltipFn}
                               filterCategoryFn={optionsContext?.groupBy === GroupOptions.CATALOGS ? filterByCatalog : filterByBandpassFilter}
                               filterCategories={optionsContext?.groupBy === GroupOptions.CATALOGS ? Object.keys(optionsContext?.selectedPlugins) : Array.from(optionsContext?.selectedBandpassFilters ?? []).sort()}
                               zoomToCoords={optionsContext?.zoomToCoords ?? null}
            />
        </div>
    )
}

export default LightCurveGlPlot;
