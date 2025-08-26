//import Plot from 'react-plotly.js';
import * as React from "react";
import type {PhotometricDataDto} from "@/features/search/lightcurve/types.ts";
import {colorFromId} from "@/utils/color.ts";
import {useContext, useEffect, useMemo} from "react";
import "@/styles/lightcurve.css";
import {OptionsContext} from "@/components/search/lightcurve/OptionsContext.tsx";
import {SetRangeContext} from './CurrentRangeContext';
import createPlotlyComponent from 'react-plotly.js/factory';
import Plotly from 'plotly.js-dist-min';

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

const unknownBand = "Unknown"


const LightCurvePlot = ({pluginNames, lightCurveData}: LightCurvePlotProps) => {
    const optionsContext = useContext(OptionsContext);
    const rangeContext = useContext(SetRangeContext);

    const sourceGroupedLcData = useMemo(() => {
        const groupedLcData: Record<string, LCData> = {};

        lightCurveData.forEach((dto) => {
            if (dto.plugin_id in groupedLcData) {
                groupedLcData[dto.plugin_id].jds.push(dto.julian_date - 2400000); // convert to MJD
                groupedLcData[dto.plugin_id].mags.push(dto.magnitude);
                groupedLcData[dto.plugin_id].magErrors.push(dto.magnitude_error);
                groupedLcData[dto.plugin_id].bands.push(dto.light_filter ?? unknownBand)
            } else {
                groupedLcData[dto.plugin_id] = {
                    jds: [dto.julian_date - 2400000],
                    mags: [dto.magnitude],
                    magErrors: [dto.magnitude_error],
                    bands: [dto.light_filter ?? unknownBand]
                }
            }
        });

        return groupedLcData;
    }, [lightCurveData])

    const bandGroupedLcData = useMemo(() => {
        const bandGroupedLcData: Record<string, LCData> = {};

        lightCurveData.forEach((dto) => {
            if ((dto.light_filter ?? unknownBand) in bandGroupedLcData) {
                bandGroupedLcData[dto.light_filter ?? unknownBand].jds.push(dto.julian_date - 2400000); // convert to MJD
                bandGroupedLcData[dto.light_filter ?? unknownBand].mags.push(dto.magnitude);
                bandGroupedLcData[dto.light_filter ?? unknownBand].magErrors.push(dto.magnitude_error);
                bandGroupedLcData[dto.light_filter ?? unknownBand].bands.push(dto.light_filter ?? unknownBand)
            } else {
                bandGroupedLcData[dto.light_filter ?? unknownBand] = {
                    jds: [dto.julian_date - 2400000],
                    mags: [dto.magnitude],
                    magErrors: [dto.magnitude_error],
                    bands: [dto.light_filter ?? unknownBand]
                }
            }
        });

        return bandGroupedLcData;
    }, [lightCurveData])


    const plotData = useMemo(() => {
        if (optionsContext?.groupBy === "sources") {
            return Object.entries(sourceGroupedLcData).map(([plugin_id, lcData]) => {
                const hoverTemplate =
                    optionsContext?.showErrorBars ? ('JD: %{x}<br>mag = %{y:.2f} &plusmn; %{error_y.array:.3f}<br>Band: %{customdata}<br>Source: %{data.name}<extra></extra>'
                    ) : (
                        'JD: %{x}<br>mag = %{y:.2f}<br>Band: %{customdata}<br>Source: %{data.name}<extra></extra>'
                    )
                return {
                    x: lcData.jds,
                    y: lcData.mags,
                    customdata: lcData.bands,
                    error_y: {
                        type: "data",
                        array: lcData.magErrors,
                        visible: optionsContext?.showErrorBars,
                        // thickness: 1,
                        // width: 5,
                    },
                    type: "scattergl",
                    mode: "markers",
                    name: pluginNames[plugin_id],
                    marker: { color: colorFromId(plugin_id)},
                    hovertemplate: hoverTemplate
                    // line: { shape: "linear" },
                }
            });
        }

        return Object.entries(bandGroupedLcData).map(([band, lcData]) => {
            const hoverTemplate =
                optionsContext?.showErrorBars ? ('JD: %{x}<br>mag = %{y:.2f} &plusmn; %{error_y.array:.3f}<br>Band: %{customdata}<br>Source: %{data.name}<extra></extra>'
                ) : (
                    'JD: %{x}<br>mag = %{y:.2f}<br>Band: %{customdata}<br>Source: %{data.name}<extra></extra>'
                )
            return {
                x: lcData.jds,
                y: lcData.mags,
                customdata: lcData.bands,
                error_y: {
                    type: "data",
                    array: lcData.magErrors,
                    visible: optionsContext?.showErrorBars,
                    // thickness: 1,
                    // width: 5,
                },
                type: "scattergl",
                mode: "markers",
                name: band,
                marker: { color: colorFromId(band)},
                hovertemplate: hoverTemplate
                // line: { shape: "linear" },
            }
        });
    }, [optionsContext?.groupBy, optionsContext?.showErrorBars, sourceGroupedLcData, bandGroupedLcData])

    /*const plotRef = React.useRef<Plotly.PlotlyHTMLElement | null>(null);

    // Apply programmatic zoom from OptionsContext ONCE, imperatively.
    useEffect(() => {
        console.log(("fdsfdsfsd"))
        if (!plotRef.current) return;
        const hasBounds = optionsContext?.minRange !== undefined && optionsContext?.maxRange !== undefined;

        if (hasBounds) {
            Plotly.relayout(plotRef.current, {
                "xaxis.range": [100, 200],
            });
        } else {
            Plotly.relayout(plotRef.current, { "xaxis.autorange": true });
        }
    }, [optionsContext?.minRange, optionsContext?.maxRange]);*/

    /*const gdRef = React.useRef<Plotly.PlotlyHTMLElement | null>(null);

    const handleInitialized = React.useCallback((_figure: any, graphDiv: Plotly.PlotlyHTMLElement) => {
        gdRef.current = graphDiv;
    }, []);

    const handleUpdate = React.useCallback((_figure: any, graphDiv: Plotly.PlotlyHTMLElement) => {
        gdRef.current = graphDiv; // keep it fresh after prop-driven updates
    }, []);

    React.useLayoutEffect(() => {
        // sanity log
        console.log('apply programmatic zoom');

        const gd = gdRef.current;
        if (!gd) return;                       // not initialized yet
        console.log("bbb")

        if (!gd._fullLayout?.xaxis) return;    // axis not ready yet (rare but safe)
        console.log("aaaa")
        const hasBounds =
            optionsContext?.minRange != null && optionsContext?.maxRange != null;

        const relayout = hasBounds
            ? { 'xaxis.range': [Number(optionsContext!.minRange), Number(optionsContext!.maxRange)] }
            : { 'xaxis.autorange': true };

        // In dev/StrictMode, guard against unmount between scheduling and run
        try {
            Plotly.relayout(gd, relayout);

        } catch (e) {

            // swallow transient errors during strict re-mounts
        }
    }, [optionsContext?.minRange, optionsContext?.maxRange]);*/

    /*useEffect(() => {
            console.log("Relayout called");
            console.log(optionsContext?.minRange, optionsContext?.maxRange);
            Plotly.relayout("lightcurve-plot", { 'xaxis.range': [Number(optionsContext!.minRange), Number(optionsContext!.maxRange)] });
    }, [optionsContext?.minRange, optionsContext?.maxRange]);*/

    const xaxis = useMemo(() => {
        return optionsContext?.minRange !== undefined && optionsContext?.maxRange !== undefined ? {
            title: {text: "Modified Julian Date in TDB"},
            type: "linear",
            range: [optionsContext?.minRange, optionsContext?.maxRange]
        } : {
            title: {text: "Modified Julian Date in TDB"},
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

    console.log("rerender")

    return (
        <Plot
            id={"lightcurve-plot"}
            //ref={plotRef as any}
            //onInitialized={handleInitialized}
            //onUpdate={handleUpdate}
            data={plotData}
            layout={{
                title: {text: "Light Curve"},
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
                modeBarButtonsToRemove: ["lasso2d", "select2d"],
            }}
            onRelayout={handleRelayout}
            //style={{ width: "100%", height: "50%" }}
        />
    );
}

// prevent the plot from rerendering, when the data has not changed
export default React.memo(LightCurvePlot);
