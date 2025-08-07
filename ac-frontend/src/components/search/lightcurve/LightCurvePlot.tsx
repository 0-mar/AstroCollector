import Plot from 'react-plotly.js';
import * as React from "react";
import type {PhotometricDataDto} from "@/features/search/lightcurve/types.ts";

type LightCurvePlotProps = {
    lightCurveData: PhotometricDataDto[]
}

const LightCurvePlot = ({lightCurveData}: LightCurvePlotProps) => {

    const jd = lightCurveData.map((data) => data.julian_date);
    const mag = lightCurveData.map((data) => data.magnitude);
    const magError = lightCurveData.map((data) => data.magnitude_error);

    return (
        <Plot
            data={[
                {
                    x: jd,
                    y: mag,
                    error_y: {
                        type: "data",
                        array: magError,
                        visible: true,
                        // thickness: 1,
                        // width: 5,
                    },
                    type: "scattergl",
                    mode: "markers",
                    // name: "Magnitude",
                    // marker: { color: "blue", size: 6 },
                    // line: { shape: "linear" },
                },
            ]}
            layout={{
                title: "Light Curve",
                xaxis: {
                    title: "Julian Date",
                    type: "linear",
                },
                yaxis: {
                    title: "Magnitude",
                    // autorange: "reversed", // Lower mag = brighter
                },
                dragmode: "pan",
                //   hovermode: "closest",
            }}
            config={{
                //   responsive: true,
                scrollZoom: true, // enables scroll zoom
                //   displaylogo: false,
                //   modeBarButtonsToRemove: ["lasso2d", "select2d"],
            }}
            style={{ width: "100%", height: "500px" }}
        />
    );
}

// prevent the plot from rerendering, when the data has not changed
export default React.memo(LightCurvePlot);
