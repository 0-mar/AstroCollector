import * as React from "react";
import {useCallback, useContext, useEffect, useState} from "react";
import type {PhaseCurveDataDto, PhotometricDataDto} from "@/features/search/photometricDataSection/types.ts";
import "@/styles/lightcurve.css";
import { OptionsContext } from "../plotOptions/OptionsContext";
import { SearchFormContext } from "@/features/search/searchSection/components/SearchFormContext";
import {ResolvedObjectCoordsContext} from "@/features/search/searchSection/components/ResolvedObjectCoordsProvider.tsx";
import { ColorsContext } from "../plotOptions/ColorsContext";
import {unknownLightFilter} from "@/features/search/photometricDataSection/components/PhotometricDataSection.tsx";
import {useQuery} from "@tanstack/react-query";
import PhaseForm from "@/features/search/photometricDataSection/components/plotOptions/PhaseForm.tsx";
import ErrorAlert from "@/features/common/alerts/ErrorAlert";
import InfoAlert from "@/features/common/alerts/InfoAlert";
import ScatterPlotDeckGl from "../scatterPlot/ScatterPlotDeckGl";
import {GroupOptions} from "@/features/search/photometricDataSection/components/plotOptions/types.ts";
import LoadingSkeleton from "@/features/common/loading/LoadingSkeleton.tsx";
import BaseApi from "@/features/common/api/baseApi.ts";


type PhaseCurveGlPlotProps = {
    data: PhotometricDataDto[],
    pluginNames: Record<string, string>
}

const PhaseCurveGlPlot = ({data, pluginNames}: PhaseCurveGlPlotProps) => {
    const optionsContext = useContext(OptionsContext);
    const colorContext = useContext(ColorsContext)
    const searchFormContext = useContext(SearchFormContext)
    const resolvedObjectCoordsContext = useContext(ResolvedObjectCoordsContext)

    const filterByCatalog = useCallback((dto: PhotometricDataDto) => dto.plugin_id, [])
    const filterByLightFilter = useCallback((dto: PhotometricDataDto) => dto.light_filter ?? unknownLightFilter, [])

    const getCatalogColor = useCallback((dto: PhotometricDataDto) => {
        return colorContext?.catalogColors[pluginNames[dto.plugin_id]] ?? [0, 0, 0]
    }, [colorContext?.catalogColors])

    const getLightFilterColor = useCallback((dto: PhotometricDataDto) => {
        return colorContext?.lightFilterColors[dto.light_filter ?? unknownLightFilter] ?? [0, 0, 0]
    }, [colorContext?.lightFilterColors])

    const tooltipFn = useCallback((dto: PhotometricDataDto | null) => {
            return (dto ? {
                text: `JD: ${xDataFn(dto).toFixed(3)}\nMag: ${dto.magnitude.toFixed(2)}\nMag Err: ${dto.magnitude_error.toFixed(3)}\nFilter: ${dto.light_filter ?? unknownLightFilter}\nCatalog: ${pluginNames[dto.plugin_id]}`
            } : null)}
        , [pluginNames])

    const [period, setPeriod] = useState(1);
    const [epoch, setEpoch] = useState(2460000);

    const fractionalPart = (n: number) => {
        const nstring = (n + "")
        const nindex  = nstring.indexOf(".")
        const result  = "0." + (nindex > -1 ? nstring.substring(nindex + 1) : "0");
        return parseFloat(result);
    }

    const xDataFn = useCallback((dto: PhotometricDataDto) => {
        return fractionalPart((dto.julian_date - epoch) / period)
    }, [period, epoch])


    const phaseDataQuery = useQuery({
        queryKey: ['phaseData', searchFormContext?.searchValues.declination, searchFormContext?.searchValues.rightAscension, resolvedObjectCoordsContext?.resolvedObjectCoords?.rightAscension, resolvedObjectCoordsContext?.resolvedObjectCoords?.declination],
        queryFn: () => BaseApi.get<PhaseCurveDataDto>('/phase-curve', searchFormContext?.searchValues.objectName !== "" ? {
            params: {
                "name": searchFormContext?.searchValues.objectName,
                "ra_deg": resolvedObjectCoordsContext?.resolvedObjectCoords?.rightAscension,
                "dec_deg": resolvedObjectCoordsContext?.resolvedObjectCoords?.declination
            }
        } : {
            params: {
                "ra_deg": searchFormContext?.searchValues.rightAscension,
                "dec_deg": searchFormContext?.searchValues.declination
            }
        }),
    })

    useEffect(() => {
        if (phaseDataQuery.isSuccess) {
            if (phaseDataQuery.data.epoch !== null) {
                setEpoch(phaseDataQuery.data.epoch);
            }
            if (phaseDataQuery.data.period !== null) {
                setPeriod(phaseDataQuery.data.period);
            }
        }
    }, [phaseDataQuery.data])

    return (
        <div className="flex flex-col p-1 shadow-md rounded-md bg-white">
            <div className={"p-4 grid grid-cols-2 gap-x-2"}>
                <PhaseForm epoch={epoch} period={period} setPeriod={setPeriod} setEpoch={setEpoch}/>
                {phaseDataQuery.isPending && <LoadingSkeleton text={"Loading phase and epoch from VSX..."}/>}
                {phaseDataQuery.isError && <ErrorAlert description={"Failed to load phase and epoch"} title={phaseDataQuery.error.message}/>}
                {phaseDataQuery.isSuccess &&
                    <InfoAlert title={"Period and Epoch from VSX catalog"}>
                        <p>Period: <span className={"font-bold"}>{phaseDataQuery.data.period ?? "No entry found"}</span></p>
                        <p>Epoch: <span className={"font-bold"}>{phaseDataQuery.data.epoch ?? "No entry found"}</span></p>
                        {phaseDataQuery.data.vsx_object_name !== null &&
                            <p>Period and epoch of object with name: <span className={"font-bold"}>{phaseDataQuery.data.vsx_object_name}</span></p>
                        }
                        <p>Phase is the fractional part of: (JD - Epoch) / Period</p>
                    </InfoAlert>}
            </div>
            <div className="bg-white shadow-md rounded-md min-h-[520px] w-full">
                <ScatterPlotDeckGl data={data}
                                   xTitle={'Phase'}
                                   yTitle={'Magnitude'}
                                   colorFn={optionsContext?.groupBy === GroupOptions.CATALOGS ? getCatalogColor : getLightFilterColor}
                                   xDataFn={xDataFn}
                                   tooltipFn={tooltipFn}
                                   filterCategoryFn={optionsContext?.groupBy === GroupOptions.CATALOGS ? filterByCatalog : filterByLightFilter}
                                   filterCategories={optionsContext?.groupBy === GroupOptions.CATALOGS ? Object.keys(optionsContext?.selectedPlugins) : Array.from(optionsContext?.selectedLightFilters ?? []).sort()}
                                   zoomToCoords={optionsContext?.zoomToCoords ?? null}
                />
            </div>
        </div>
    );
}

// prevent the plot from rerendering, when the data has not changed
export default React.memo(PhaseCurveGlPlot);
