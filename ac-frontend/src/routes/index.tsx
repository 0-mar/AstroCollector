import {createFileRoute} from '@tanstack/react-router'
import logo from '../logo.svg'
import Plot from "react-plotly.js";

export const Route = createFileRoute('/')({
    component: App,
})

function App() {
    const data = [
        {jd: 2451545.0, mag: 12.3, magError: 0.1},
        {jd: 2451546.0, mag: 12.5, magError: 0.05},
        {jd: 2451547.0, mag: 12.1, magError: 0.2},
        {jd: 2451548.0, mag: 12.4, magError: 0.15},
    ];
    for (let i = 0; i < 1000; i++) {
        data.push({jd: 2451545.0 + i, mag: 12.3 + i, magError: 0.1});
    }
    const jd = data.map((point) => point.jd);
    const mag = data.map((point) => point.mag);
    const magError = data.map((point) => point.magError);

    return (
        <div className="text-center">
            <header
                className="min-h-screen flex flex-col items-center justify-center bg-[#282c34] text-white text-[calc(10px+2vmin)]">
                <img
                    src={logo}
                    className="h-[40vmin] pointer-events-none animate-[spin_20s_linear_infinite]"
                    alt="logo"
                />
                <p>
                    Edit <code>src/routes/index.tsx</code> and save to reload.
                </p>
                <a
                    className="text-[#61dafb] hover:underline"
                    href="https://reactjs.org"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    Learn React
                </a>
                <a
                    className="text-[#61dafb] hover:underline"
                    href="https://tanstack.com"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    Learn TanStack
                </a>

            </header>
            <div className="w-full h-[500px] text-left border border-red-500">
                fdsfds
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
                        name: "Magnitude",
                        marker: {color: "blue", size: 6},
                        line: {shape: "linear"},
                    },
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
                        name: "FDSFSD",
                        marker: {color: "#3b547d", size: 9},
                        line: {shape: "linear"},
                    },
                ]}
                layout={{
                    title: "Light Curve",
                    xaxis: {
                        title: {text: "Julian Date"},
                        automargin: true
                        // type: "linear",
                    },
                    yaxis: {
                        title: "Magnitude",
                        autorange: "reversed", // Lower mag = brighter
                        automargin: true
                    },
                    dragmode: "pan",
                    margin: { t: 40, b: 60, l: 60, r: 20 },
                    //   hovermode: "closest",
                }}
                config={{
                    responsive: true,
                    scrollZoom: true, // enables scroll zoom
                    displaylogo: false,
                    modeBarButtonsToRemove: ["lasso2d", "select2d"],
                }}
                className="w-full h-[500px]"
            />
            </div>

        </div>
    )
}
