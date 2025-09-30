// import * as React from "react";
// import type {PhotometricDataDto} from "@/features/search/photometricDataSection/types.ts";
// import {colorFromId} from "@/utils/color.ts";
// import {useContext, useMemo} from "react";
// import "@/styles/lightcurve.css";
// import {OptionsContext} from "@/components/search/photometricData/plotOptions/OptionsContext.tsx";
// import {SetRangeContext} from '../plotOptions/CurrentRangeContext.tsx';
// import createPlotlyComponent from 'react-plotly.js/factory';
// import Plotly from 'plotly.js-dist-min';
//
// const enSpace = {
//     moduleType: 'locale',
//     name: 'en-space',
//     dictionary: {},
//     format: {
//         decimal: '.',
//         thousands: ' ',
//         grouping: [3],
//         currency: ['$', ''],
//
//         dateTime: '%A, %B %e, %Y %X',
//         date: '%m/%d/%Y',
//         time: '%I:%M:%S %p',
//         periods: ['AM', 'PM'],
//         days: ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'],
//         shortDays: ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'],
//         months: [
//             'January','February','March','April','May','June',
//             'July','August','September','October','November','December'
//         ],
//         shortMonths: ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
//     }
// };
// Plotly.register(enSpace);
// Plotly.setPlotConfig({ locale: 'en-space' });
//
// const Plot = createPlotlyComponent(Plotly);
//
// type LightCurvePlotProps = {
//     pluginNames: Record<string, string>,
//     lightCurveData: PhotometricDataDto[]
// }
//
// type LCData = {
//     jds: number[],
//     mags: number[],
//     magErrors: number[],
//     bands: string[]
// }
//
// const unknownBand = "Unknown"
//
//
// const LightCurvePlot = ({pluginNames, lightCurveData}: LightCurvePlotProps) => {
//     const optionsContext = useContext(OptionsContext);
//     const rangeContext = useContext(SetRangeContext);
//
//     const transformJD = (jd: number) => jd - 2400000 // shortened JD version, do not confuse with MJD!
//     const addEntry = (data: Record<string, LCData>, key: string, dto: PhotometricDataDto) => {
//         if (key in data) {
//             data[key].jds.push(transformJD(dto.julian_date));
//             data[key].mags.push(dto.magnitude);
//             data[key].magErrors.push(dto.magnitude_error);
//             data[key].bands.push(dto.light_filter ?? unknownBand)
//         } else {
//             data[key] = {
//                 jds: [transformJD(dto.julian_date)],
//                 mags: [dto.magnitude],
//                 magErrors: [dto.magnitude_error],
//                 bands: [dto.light_filter ?? unknownBand]
//             }
//         }
//     }
//
//     // create grouped sets of plot points - by source, band
//     const [sourceGroupedLcData, bandGroupedLcData] = useMemo(() => {
//         const sourceGroupedLcData: Record<string, LCData> = {};
//         const bandGroupedLcData: Record<string, LCData> = {};
//
//         lightCurveData.forEach((dto) => addEntry(sourceGroupedLcData, dto.plugin_id, dto));
//         lightCurveData.forEach((dto) => addEntry(bandGroupedLcData, dto.light_filter ?? unknownBand, dto));
//
//         return [sourceGroupedLcData, bandGroupedLcData];
//     }, [lightCurveData])
//
//     const plotData = useMemo(() => {
//         const hoverTemplate =
//             optionsContext?.showErrorBars ? ('JD: %{x:,.1f}<br>mag = %{y:.2f} &plusmn; %{error_y.array:.3f}<br>Band: %{customdata}<br>Source: %{data.name}<extra></extra>'
//             ) : (
//                 'JD: %{x:,.1f}<br>mag = %{y:.2f}<br>Band: %{customdata}<br>Source: %{data.name}<extra></extra>'
//             )
//
//         const groupedData = optionsContext?.groupBy === "sources" ? sourceGroupedLcData : bandGroupedLcData;
//
//         const buildTrace = (key: string, lcData: LCData) => ({
//             x: lcData.jds,
//             y: lcData.mags,
//             customdata: lcData.bands,
//             error_y: {
//                 type: "data" as const,
//                 array: lcData.magErrors,
//                 visible: optionsContext?.showErrorBars,
//             },
//             type: "scattergl" as const,
//             mode: "markers" as const,
//             name: optionsContext?.groupBy === "sources" ? pluginNames[key] : key,
//             marker: {color: colorFromId(key)},
//             hovertemplate: hoverTemplate,
//         });
//
//         return Object.entries(groupedData).map(([key, lcData]) => buildTrace(key, lcData));
//     }, [optionsContext?.groupBy, optionsContext?.showErrorBars, sourceGroupedLcData, bandGroupedLcData, pluginNames])
//
//     const xaxis = useMemo(() => {
//         return optionsContext?.minRange !== undefined && optionsContext?.maxRange !== undefined ? {
//             title: {text: "Julian Date - 2400000 in TDB"},
//             type: "linear",
//             tickformat: ',.1f',
//             range: [optionsContext?.minRange, optionsContext?.maxRange]
//         } : {
//             title: {text: "Julian Date - 2400000 in TDB"},
//             type: "linear",
//             tickformat: ',.1f',
//             autorange: true
//         }
//     }, [optionsContext?.minRange, optionsContext?.maxRange, optionsContext?.plotVersion]);
//
//     const handleRelayout = (eventData: any) => {
//         const newMin = eventData["xaxis.range[0]"];
//         const newMax = eventData["xaxis.range[1]"];
//
//         if (newMin !== undefined && newMax !== undefined) {
//             rangeContext?.setCurrMaxRange(Number(newMax))
//             rangeContext?.setCurrMinRange(Number(newMin))
//         }
//     };
//
//     return (
//         <div className="p-1 shadow-md rounded-md bg-white">
//             <Plot
//                 data={plotData}
//                 layout={{
//                     title: {text: "Light Curve"},
//                     xaxis: xaxis,
//                     yaxis: {
//                         title: {text: "Magnitude"},
//                         autorange: "reversed", // Lower mag = brighter
//                     },
//                     dragmode: "pan",
//                     //   hovermode: "closest",
//                 }}
//                 config={{
//                     responsive: true,
//                     scrollZoom: true,
//                     displaylogo: false,
//                     modeBarButtonsToRemove: ["lasso2d", "select2d", "resetScale2d"],
//                     displayModeBar: true
//                 }}
//                 onRelayout={handleRelayout}
//                 style={{width: "100%", height: "100%"}}
//             />
//         </div>
//     );
// }
//
// // prevent the plot from rerendering, when the data has not changed
// export default React.memo(LightCurvePlot);


import * as React from "react";
import type {PhotometricDataDto} from "@/features/search/photometricDataSection/types.ts";
import {colorFromId} from "@/utils/color.ts";
import {useContext, useMemo, useRef, useEffect, useState} from "react";
import "@/styles/lightcurve.css";
import {OptionsContext} from "@/components/search/photometricData/plotOptions/OptionsContext.tsx";
import {RangeContext, SetRangeContext} from '../plotOptions/CurrentRangeContext.tsx';
import createPlotlyComponent from 'react-plotly.js/factory';
import Plotly from 'plotly.js-dist-min';
import {lowerBound, lttb, upperBound} from "@/features/search/photometricDataSection/utils.ts";

const enSpace = {
    moduleType: 'locale',
    name: 'en-space',
    dictionary: {},
    format: {
        decimal: '.',
        thousands: ' ',
        grouping: [3],
        currency: ['$', ''],
        dateTime: '%A, %B %e, %Y %X',
        date: '%m/%d/%Y',
        time: '%I:%M:%S %p',
        periods: ['AM', 'PM'],
        days: ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'],
        shortDays: ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'],
        months: [
            'January','February','March','April','May','June',
            'July','August','September','October','November','December'
        ],
        shortMonths: ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    }
};
Plotly.register(enSpace);
Plotly.setPlotConfig({ locale: 'en-space' });

const Plot = createPlotlyComponent(Plotly);

type LightCurvePlotProps = {
    pluginNames: Record<string, string>,
    lightCurveData: PhotometricDataDto[]
}

type LCData = {
    jds: number[],
    mags: number[],
    magErrors: number[],
    bands: string[]
}

const unknownBand = "Unknown";

const LightCurvePlot = ({pluginNames, lightCurveData}: LightCurvePlotProps) => {
    const optionsContext = useContext(OptionsContext);
    const rangeContext = useContext(SetRangeContext);
    const getRangeContext = useContext(RangeContext)

    const transformJD = (jd: number) => jd - 2400000; // shortened JD version, do not confuse with MJD!
    const addEntry = (data: Record<string, LCData>, key: string, dto: PhotometricDataDto) => {
        if (key in data) {
            data[key].jds.push(transformJD(dto.julian_date));
            data[key].mags.push(dto.magnitude);
            data[key].magErrors.push(dto.magnitude_error);
            data[key].bands.push(dto.light_filter ?? unknownBand);
        } else {
            data[key] = {
                jds: [transformJD(dto.julian_date)],
                mags: [dto.magnitude],
                magErrors: [dto.magnitude_error],
                bands: [dto.light_filter ?? unknownBand]
            };
        }
    };

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

    // Group by source/band (raw data)
    const [sourceGroupedLcData, bandGroupedLcData] = useMemo(() => {
        const sourceGroupedLcData: Record<string, LCData> = {};
        const bandGroupedLcData: Record<string, LCData> = {};
        downsampledData.forEach((dto) => addEntry(sourceGroupedLcData, dto.plugin_id, dto));
        downsampledData.forEach((dto) => addEntry(bandGroupedLcData, dto.light_filter ?? unknownBand, dto));
        return [sourceGroupedLcData, bandGroupedLcData];
    }, [downsampledData]);

    const plotData = useMemo(() => {
        const hoverTemplate =
            optionsContext?.showErrorBars
                ? 'JD: %{x:,.1f}<br>mag = %{y:.2f} &plusmn; %{error_y.array:.3f}<br>Band: %{customdata}<br>Source: %{data.name}<extra></extra>'
                : 'JD: %{x:,.1f}<br>mag = %{y:.2f}<br>Band: %{customdata}<br>Source: %{data.name}<extra></extra>';

        const groupedData = optionsContext?.groupBy === "sources" ? sourceGroupedLcData : bandGroupedLcData;

        const buildTrace = (key: string, lcData: LCData) => ({
            x: lcData.jds,
            y: lcData.mags,
            customdata: lcData.bands,
            error_y: {
                type: "data" as const,
                array: lcData.magErrors,
                visible: optionsContext?.showErrorBars,
            },
            type: "scattergl" as const,
            mode: "markers" as const,
            //visible: "false" as const,
            name: optionsContext?.groupBy === "sources" ? pluginNames[key] : key,
            marker: {color: colorFromId(key)},
            hovertemplate: hoverTemplate,
        });

        return Object.entries(groupedData).map(([key, lcData]) => buildTrace(key, lcData));
    }, [
        optionsContext?.groupBy,
        optionsContext?.showErrorBars,
        sourceGroupedLcData,
        bandGroupedLcData,
        pluginNames,
    ]);

    const xaxis = useMemo(() => {
        return (optionsContext?.minRange !== undefined && optionsContext?.maxRange !== undefined)
            ? {
                title: { text: "Julian Date - 2400000 in TDB" },
                type: "linear",
                tickformat: ',.1f',
                range: [optionsContext?.minRange, optionsContext?.maxRange]
            }
            : {
                title: { text: "Julian Date - 2400000 in TDB" },
                type: "linear",
                tickformat: ',.1f',
                autorange: true
            };
    }, [optionsContext?.minRange, optionsContext?.maxRange, optionsContext?.plotVersion]);

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
        <div ref={containerRef} className="p-1 shadow-md rounded-md bg-white h-[450px]">
            <Plot
                className={"w-full h-[420px]"}
                data={plotData}
                layout={{
                    title: { text: "Light Curve" },
                    xaxis: xaxis,
                    yaxis: {
                        title: { text: "Magnitude" },
                        autorange: "reversed", // Lower mag = brighter
                    },
                    dragmode: "pan",
                    uirevision: "lc-static",   // preserve zoom/selection on prop changes
                }}
                config={{
                    responsive: true,
                    scrollZoom: true,
                    displaylogo: false,
                    modeBarButtonsToRemove: ["lasso2d", "select2d", "resetScale2d"],
                    displayModeBar: true
                }}
                onRelayout={handleRelayout}
            />
        </div>
    );
};

export default React.memo(LightCurvePlot);
