import {useCallback, useContext} from "react";
import type { PhotometricDataDto } from "../../types.ts";
import {OptionsContext} from "../plotOptions/OptionsContext.tsx";
import {ColorsContext} from "@/features/search/photometricDataSection/components/plotOptions/ColorsContext.tsx";
import { unknownLightFilter } from "../PhotometricDataSection.tsx";
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
    const filterByLightFilter = useCallback((dto: PhotometricDataDto) => dto.light_filter ?? unknownLightFilter, [])

    const getCatalogColor = useCallback((dto: PhotometricDataDto) => {
        return colorContext?.catalogColors[pluginNames[dto.plugin_id]] ?? [0, 0, 0]
    }, [colorContext?.catalogColors])

    const getLightFilterColor = useCallback((dto: PhotometricDataDto) => {
        return colorContext?.lightFilterColors[dto.light_filter ?? unknownLightFilter] ?? [0, 0, 0]
    }, [colorContext?.lightFilterColors])

    const xDataFn = useCallback((dto: PhotometricDataDto) => {
        return dto.julian_date - 2400000
    }, [])

    const tooltipFn = useCallback((dto: PhotometricDataDto | null) => {
        return (dto ? {
            text: `JD: ${xDataFn(dto).toFixed(3)}\nMag: ${dto.magnitude.toFixed(2)}\nMag Err: ${dto.magnitude_error.toFixed(3)}\nFilter: ${dto.light_filter ?? unknownLightFilter}\nCatalog: ${pluginNames[dto.plugin_id]}`
        } : null)}
        , [pluginNames])

    return (
        <div className="bg-white shadow-md rounded-md min-h-[520px] w-full">
            <ScatterPlotDeckGl data={data}
                               xTitle={'Julian Date - 2400000 in TDB'}
                               yTitle={'Magnitude'}
                               colorFn={optionsContext?.groupBy === GroupOptions.CATALOGS ? getCatalogColor : getLightFilterColor}
                               xDataFn={xDataFn}
                               tooltipFn={tooltipFn}
                               filterCategoryFn={optionsContext?.groupBy === GroupOptions.CATALOGS ? filterByCatalog : filterByLightFilter}
                               filterCategories={optionsContext?.groupBy === GroupOptions.CATALOGS ? Object.keys(optionsContext?.selectedPlugins) : Array.from(optionsContext?.selectedLightFilters ?? []).sort()}
                               zoomToCoords={optionsContext?.zoomToCoords ?? null}
            />
        </div>
    )
}

export default LightCurveGlPlot;
