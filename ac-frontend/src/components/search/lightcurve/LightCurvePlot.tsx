import Plot from 'react-plotly.js';
import * as React from "react";
import type {PhotometricDataDto} from "@/features/search/lightcurve/types.ts";
import {colorFromId} from "@/utils/color.ts";
import {useMemo} from "react";

type LightCurvePlotProps = {
    showErrorBars: boolean,
    pluginNames: Record<string, string>,
    lightCurveData: PhotometricDataDto[]
    groupBy: string,
}

type LCData = {
    jds: number[],
    mags: number[],
    magErrors: number[],
    bands: string[]
}

const unknownBand = "Unknown"


const LightCurvePlot = ({showErrorBars, pluginNames, lightCurveData, groupBy}: LightCurvePlotProps) => {

    //const jd = lightCurveData.map((data) => data.julian_date);
    //const mag = lightCurveData.map((data) => data.magnitude);
    //const magError = lightCurveData.map((data) => data.magnitude_error);

    const sourceGroupedLcData = useMemo(() => {
        const groupedLcData: Record<string, LCData> = {};

        lightCurveData.forEach((dto) => {
            if (dto.plugin_id in groupedLcData) {
                groupedLcData[dto.plugin_id].jds.push(dto.julian_date);
                groupedLcData[dto.plugin_id].mags.push(dto.magnitude);
                groupedLcData[dto.plugin_id].magErrors.push(dto.magnitude_error);
                groupedLcData[dto.plugin_id].bands.push(dto.light_filter ?? unknownBand)
            } else {
                groupedLcData[dto.plugin_id] = {
                    jds: [dto.julian_date],
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
                bandGroupedLcData[dto.light_filter ?? unknownBand].jds.push(dto.julian_date);
                bandGroupedLcData[dto.light_filter ?? unknownBand].mags.push(dto.magnitude);
                bandGroupedLcData[dto.light_filter ?? unknownBand].magErrors.push(dto.magnitude_error);
                bandGroupedLcData[dto.light_filter ?? unknownBand].bands.push(dto.light_filter ?? unknownBand)
            } else {
                bandGroupedLcData[dto.light_filter ?? unknownBand] = {
                    jds: [dto.julian_date],
                    mags: [dto.magnitude],
                    magErrors: [dto.magnitude_error],
                    bands: [dto.light_filter ?? unknownBand]
                }
            }
        });

        return bandGroupedLcData;
    }, [lightCurveData])


    const plotData = useMemo(() => {
        if (groupBy === "sources") {
            return Object.entries(sourceGroupedLcData).map(([plugin_id, lcData]) => {
                const hoverTemplate =
                    showErrorBars ? ('JD: %{x}<br>mag = %{y:.2f} &plusmn; %{error_y.array:.3f}<br>Band: %{customdata}<br>Source: %{data.name}<extra></extra>'
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
                        visible: showErrorBars,
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
                showErrorBars ? ('JD: %{x}<br>mag = %{y:.2f} &plusmn; %{error_y.array:.3f}<br>Band: %{customdata}<br>Source: %{data.name}<extra></extra>'
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
                    visible: showErrorBars,
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
    }, [groupBy, showErrorBars, sourceGroupedLcData, bandGroupedLcData])


    /*const data: Record<string, LCData> = {};
    lightCurveData.forEach((dto) => {
        if (dto.plugin_id in data) {
            data[dto.plugin_id].jds.push(dto.julian_date);
            data[dto.plugin_id].mags.push(dto.magnitude);
            data[dto.plugin_id].magErrors.push(dto.magnitude_error);
        } else {
            pluginColors[dto.plugin_id] = generateColor();
            setPluginColors(pluginColors)
            data[dto.plugin_id] = {
                jds: [dto.julian_date],
                mags: [dto.magnitude],
                magErrors: [dto.magnitude_error],
            }
        }
    });
    console.log(pluginColors)

    const plotData = Object.entries(data).map(([plugin_id, lcData]) => {
        return {
        x: lcData.jds,
            y: lcData.mags,
            error_y: {
                type: "data",
                array: lcData.magErrors,
                visible: showErrorBars,
                // thickness: 1,
                // width: 5,
            },
            type: "scattergl",
            mode: "markers",
            name: plugin_id,
            marker: { color: pluginColors[plugin_id]},
            // line: { shape: "linear" },
        }
    });*/


    /*[
        {
            x: jd,
            y: mag,
            error_y: {
                type: "data",
                array: magError,
                visible: showErrorBars,
                // thickness: 1,
                // width: 5,
            },
            type: "scattergl",
            mode: "markers",
            // name: "Magnitude",
            // marker: { color: "blue", size: 6 },
            // line: { shape: "linear" },
        },
    ]*/

    return (
        <Plot
            data={plotData}
            layout={{
                title: {text: "Light Curve"},
                xaxis: {
                    title: {text: "Julian Date"},
                    type: "linear",
                },
                yaxis: {
                    title: {text: "Magnitude"},
                    autorange: "reversed", // Lower mag = brighter
                },
                dragmode: "pan",
                //   hovermode: "closest",
            }}
            config={{
                responsive: true,
                scrollZoom: true, // enables scroll zoom
                displaylogo: false,
                //   modeBarButtonsToRemove: ["lasso2d", "select2d"],
            }}
            style={{ width: "100%", height: "500px" }}
        />
    );
}

// prevent the plot from rerendering, when the data has not changed
export default React.memo(LightCurvePlot);
// export default LightCurvePlot;
