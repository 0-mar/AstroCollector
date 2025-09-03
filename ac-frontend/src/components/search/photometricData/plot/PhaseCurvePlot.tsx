import * as React from "react";
import {useContext, useMemo} from "react";
import type {PhaseCurveDataDto, PhotometricDataDto} from "@/features/search/lightcurve/types.ts";
import {colorFromId} from "@/utils/color.ts";
import "@/styles/lightcurve.css";
import {OptionsContext} from "@/components/search/photometricData/plotOptions/OptionsContext.tsx";
import {SetRangeContext} from '../plotOptions/CurrentRangeContext.tsx';
import createPlotlyComponent from 'react-plotly.js/factory';
import Plotly from 'plotly.js-dist-min';
import {useQuery} from "@tanstack/react-query";
import BaseApi from "@/features/api/baseApi.ts";
import {SearchFormContext} from "@/components/search/form/SearchFormContext.tsx";
import {ObjectCoordsContext} from "@/components/search/form/ObjectCoordsProvider.tsx";
import LoadingSkeleton from "@/components/loading/LoadingSkeleton.tsx";
import ErrorAlert from "@/components/alerts/ErrorAlert.tsx";
import InfoAlert from "@/components/alerts/InfoAlert.tsx";

const Plot = createPlotlyComponent(Plotly);

type PhaseCurvePlotProps = {
    pluginNames: Record<string, string>,
    lightCurveData: PhotometricDataDto[]
}

type PhaseCurveData = {
    phases: number[],
    mags: number[],
    magErrors: number[],
    bands: string[]
}

const unknownBand = "Unknown"

const PhaseCurvePlot = ({pluginNames, lightCurveData}: PhaseCurvePlotProps) => {
    const optionsContext = useContext(OptionsContext);
    const rangeContext = useContext(SetRangeContext);
    const searchFormContext = useContext(SearchFormContext)
    const objectCoordsContext = useContext(ObjectCoordsContext)

    const computePhase = (jd: number, epoch: number, period: number) => (jd - epoch) / period
    const addEntry = (data: Record<string, PhaseCurveData>, key: string, dto: PhotometricDataDto) => {
        if (key in data) {
            data[key].phases.push(computePhase(dto.julian_date, phaseDataQuery.data?.epoch ?? 0, phaseDataQuery.data?.period ?? 0));
            data[key].mags.push(dto.magnitude);
            data[key].magErrors.push(dto.magnitude_error);
            data[key].bands.push(dto.light_filter ?? unknownBand)
        } else {
            data[key] = {
                phases: [computePhase(dto.julian_date, phaseDataQuery.data?.epoch ?? 0, phaseDataQuery.data?.period ?? 0)],
                mags: [dto.magnitude],
                magErrors: [dto.magnitude_error],
                bands: [dto.light_filter ?? unknownBand]
            }
        }
    }

    const phaseDataQuery = useQuery({
        queryKey: ['phaseData', searchFormContext?.searchValues.declination, searchFormContext?.searchValues.rightAscension, objectCoordsContext?.objectCoords.rightAscension, objectCoordsContext?.objectCoords.declination],
        queryFn: () => BaseApi.get<PhaseCurveDataDto>('/phase-curve', searchFormContext?.searchValues.objectName !== "" ? {
            params: {
                "name": searchFormContext?.searchValues.objectName,
                "ra_deg": objectCoordsContext?.objectCoords.rightAscension,
                "dec_deg": objectCoordsContext?.objectCoords.declination
            }
        } : {
            params: {
                "ra_deg": searchFormContext?.searchValues.rightAscension,
                "dec_deg": searchFormContext?.searchValues.declination
            }
        }),
    })

    const [sourceGroupedLcData, bandGroupedLcData] = useMemo(() => {
        const sourceGroupedLcData: Record<string, PhaseCurveData> = {};
        const bandGroupedLcData: Record<string, PhaseCurveData> = {};

        if (!phaseDataQuery.isSuccess) {
            return [sourceGroupedLcData, bandGroupedLcData]
        }
        if (phaseDataQuery.data?.epoch === null || phaseDataQuery.data?.period === null) {
            return [sourceGroupedLcData, bandGroupedLcData]
        }

        lightCurveData.forEach((dto) => addEntry(sourceGroupedLcData, dto.plugin_id, dto));
        lightCurveData.forEach((dto) => addEntry(bandGroupedLcData, dto.light_filter ?? unknownBand, dto));

        return [sourceGroupedLcData, bandGroupedLcData];
    }, [lightCurveData, phaseDataQuery.status])


    const plotData = useMemo(() => {

        const hoverTemplate =
            optionsContext?.showErrorBars ? ('Phase: %{x}<br>mag = %{y:.2f} &plusmn; %{error_y.array:.3f}<br>Band: %{customdata}<br>Source: %{data.name}<extra></extra>'
            ) : (
                'Phase: %{x}<br>mag = %{y:.2f}<br>Band: %{customdata}<br>Source: %{data.name}<extra></extra>'
            )

        const groupedData = optionsContext?.groupBy === "sources" ? sourceGroupedLcData : bandGroupedLcData;

        const buildTrace = (key: string, lcData: PhaseCurveData) => ({
            x: lcData.phases,
            y: lcData.mags,
            customdata: lcData.bands,
            error_y: {
                type: "data" as const,
                array: lcData.magErrors,
                visible: optionsContext?.showErrorBars,
            },
            type: "scattergl" as const,
            mode: "markers" as const,
            name: optionsContext?.groupBy === "sources" ? pluginNames[key] : key,
            marker: {color: colorFromId(key)},
            hovertemplate: hoverTemplate,
        });

        return Object.entries(groupedData).map(([key, lcData]) => buildTrace(key, lcData));
    }, [optionsContext?.groupBy, optionsContext?.showErrorBars, sourceGroupedLcData, bandGroupedLcData, pluginNames])

    const xaxis = useMemo(() => {
        return optionsContext?.minRange !== undefined && optionsContext?.maxRange !== undefined ? {
            title: {text: "Phase"},
            type: "linear",
            range: [optionsContext?.minRange, optionsContext?.maxRange]
        } : {
            title: {text: "Phase"},
            type: "linear",
            autorange: true
        }
    }, [optionsContext?.minRange, optionsContext?.maxRange, optionsContext?.plotVersion]);

    const handleRelayout = (eventData: any) => {
        const newMin = eventData["xaxis.range[0]"];
        const newMax = eventData["xaxis.range[1]"];

        if (newMin !== undefined && newMax !== undefined) {
            rangeContext?.setCurrMaxRange(Number(newMax))
            rangeContext?.setCurrMinRange(Number(newMin))
        }
    };

    if (phaseDataQuery.isPending) {
        return <LoadingSkeleton text={"Loading phase and epoch..."}/>
    }

    if (phaseDataQuery.isError) {
        return <ErrorAlert description={"Failed to load phase and epoch"} title={phaseDataQuery.error.message}/>
    }

    if (phaseDataQuery.data.epoch === null || phaseDataQuery.data.period === null) {
        return <ErrorAlert description={"Phase and epoch is not available in VSX"} title={"Unable to display phase curve"}/>
    }

    return (
        <div className="flex flex-col p-1 shadow-md rounded-md bg-white">
            <InfoAlert title={"Period and Epoch from VSX catalog"}>
                <p>Period: <span className={"font-bold"}>{phaseDataQuery.data.period}</span></p>
                <p>Epoch: <span className={"font-bold"}>{phaseDataQuery.data.epoch}</span></p>
                <p>Period and epoch of object with name: <span className={"font-bold"}>{phaseDataQuery.data.vsx_object_name}</span></p>
                <p>Phase is computed as: (JD - Epoch) / Period</p>
            </InfoAlert>
            <Plot
                data={plotData}
                layout={{
                    title: {text: "Phase Curve"},
                    xaxis: xaxis,
                    yaxis: {
                        title: {text: "Magnitude"},
                        autorange: "reversed", // Lower mag = brighter
                    },
                    dragmode: "pan",
                    //   hovermode: "closest",
                }}
                config={{
                    responsive: true,
                    scrollZoom: true,
                    displaylogo: false,
                    modeBarButtonsToRemove: ["lasso2d", "select2d", "resetScale2d"],
                    displayModeBar: true
                }}
                onRelayout={handleRelayout}
                style={{width: "100%", height: "100%"}}
            />
        </div>
    );
}

// prevent the plot from rerendering, when the data has not changed
export default React.memo(PhaseCurvePlot);
