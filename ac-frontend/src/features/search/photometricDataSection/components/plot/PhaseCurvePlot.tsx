import * as React from "react";
import {useContext, useEffect, useMemo, useRef, useState} from "react";
import type {PhaseCurveDataDto, PhotometricDataDto} from "@/features/search/photometricDataSection/types.ts";
import {colorFromId} from "@/utils/color.ts";
import "@/styles/lightcurve.css";
import {OptionsContext} from "@/features/search/photometricDataSection/components/plotOptions/OptionsContext.tsx";
import {RangeContext, SetRangeContext} from '../plotOptions/CurrentRangeContext.tsx';
import createPlotlyComponent from 'react-plotly.js/factory';
import Plotly from 'plotly.js-dist-min';
import {useQuery} from "@tanstack/react-query";
import BaseApi from "@/features/common/api/baseApi.ts";
import {SearchFormContext} from "@/features/search/searchSection/components/SearchFormContext.tsx";
import {ObjectCoordsContext} from "@/features/search/searchSection/components/ObjectCoordsProvider.tsx";
import LoadingSkeleton from "@/features/common/loading/LoadingSkeleton.tsx";
import ErrorAlert from "@/features/common/alerts/ErrorAlert.tsx";
import InfoAlert from "@/features/common/alerts/InfoAlert.tsx";
import PhaseForm from "@/features/search/photometricDataSection/components/plotOptions/PhaseForm.tsx";
import {lowerBound, lttb, upperBound} from "@/features/search/photometricDataSection/utils.ts";

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
    const getRangeContext = useContext(RangeContext)
    const searchFormContext = useContext(SearchFormContext)
    const objectCoordsContext = useContext(ObjectCoordsContext)

    const [period, setPeriod] = useState(1);
    const [epoch, setEpoch] = useState(2460000);

    const fractionalPart = (n: number) => {
        const nstring = (n + "")
        const nindex  = nstring.indexOf(".")
        const result  = "0." + (nindex > -1 ? nstring.substring(nindex + 1) : "0");
        return parseFloat(result);
    }
    const computePhase = (jd: number, epoch: number, period: number) => fractionalPart((jd - epoch) / period)
    const addEntry = (data: Record<string, PhaseCurveData>, key: string, dto: PhotometricDataDto) => {
        if (key in data) {
            data[key].phases.push(computePhase(dto.julian_date, epoch, period));
            data[key].mags.push(dto.magnitude);
            data[key].magErrors.push(dto.magnitude_error);
            data[key].bands.push(dto.light_filter ?? unknownBand)
        } else {
            data[key] = {
                phases: [computePhase(dto.julian_date, epoch, period)],
                mags: [dto.magnitude],
                magErrors: [dto.magnitude_error],
                bands: [dto.light_filter ?? unknownBand]
            }
        }
    }

    const sortedData = useMemo(() => {
        return lightCurveData.sort((a, b) => a.julian_date - b.julian_date);
    }, [lightCurveData])

    // Observe container width for viewport-aware decimation target
    const containerRef = useRef<HTMLDivElement | null>(null);
    const [plotWidth, setPlotWidth] = useState(800);
    useEffect(() => {
        const el = containerRef.current;
        if (!el) return;
        const ro = new ResizeObserver(([entry]) => {
            setPlotWidth(Math.max(300, Math.floor(entry.contentRect.width)));
        });
        ro.observe(el);
        return () => ro.disconnect();
    }, []);

    // 3 points per pixel
    const targetPoints = useMemo(() => {console.log(Math.max(800, Math.min(4000, plotWidth * 3))); return Math.max(800, Math.min(4000, plotWidth * 3))}, [plotWidth]);

    const downsampledData = useMemo(() => {
        let lower = 0;
        let upper = sortedData.length;

        if (getRangeContext?.currMinRange !== undefined && getRangeContext?.currMaxRange !== undefined) {
            lower = Math.max(0, lowerBound(sortedData, getRangeContext?.currMinRange + 2400000));
            upper = Math.min(sortedData.length, upperBound(sortedData, getRangeContext?.currMaxRange + 2400000));
        }

        const threshold = targetPoints;
        return lttb(sortedData, lower, upper, threshold)
    }, [sortedData,
        getRangeContext?.currMinRange,
        getRangeContext?.currMaxRange])

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

        downsampledData.forEach((dto) => addEntry(sourceGroupedLcData, dto.plugin_id, dto));
        downsampledData.forEach((dto) => addEntry(bandGroupedLcData, dto.light_filter ?? unknownBand, dto));

        return [sourceGroupedLcData, bandGroupedLcData];
    }, [downsampledData, epoch, period])


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
    }, [optionsContext?.groupBy,
        optionsContext?.showErrorBars,
        sourceGroupedLcData,
        bandGroupedLcData,
        pluginNames])

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


    // Relayout: update current visible range
    const relayoutRAF = useRef<number | null>(null);
    const handleRelayout = (eventData: any) => {
        if (relayoutRAF.current) cancelAnimationFrame(relayoutRAF.current);
        relayoutRAF.current = requestAnimationFrame(() => {
            const r0 = eventData["xaxis.range[0]"];
            const r1 = eventData["xaxis.range[1]"];
            if (r0 !== undefined && r1 !== undefined) {
                rangeContext?.setCurrMinRange(Number(r0));
                rangeContext?.setCurrMaxRange(Number(r1));
            }
        });
    };

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
            <div ref={containerRef} className="p-1 shadow-md rounded-md bg-white h-[450px]">
                <Plot
                    className={"w-full h-[420px]"}
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
        </div>
    );
}

// prevent the plot from rerendering, when the data has not changed
export default React.memo(PhaseCurvePlot);
