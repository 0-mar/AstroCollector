import {createFileRoute} from '@tanstack/react-router'

export const Route = createFileRoute('/about')({
    component: RouteComponent,
})

function RouteComponent() {
    return (
        <>
            <div className="bg-blue-100">
                <div className="p-8 flex flex-col gap-y-2">
                    <h1 className={"text-3xl font-extrabold"}>About</h1>
                    <p><span className="font-extrabold text-lg text-transparent bg-clip-text bg-gradient-to-r to-black from-amber-400">AstroCollector</span> is a tool for searching for photometric data of stellar objects. It allows users to display and download data from various star surveys / catalogs.
                    </p>
                    <p>
                        The tool was developed for the <a href={"https://www.physics.muni.cz/en"} target={"_blank"} className={"font-medium text-blue-600 hover:underline"}>Department of Physics, Faculty of Science, Masaryk university</a>.
                    </p>
                </div>
            </div>
            <div className="bg-white">
                <div className="p-8 flex flex-col gap-y-2">
                    <h2 className={"text-xl font-bold"}>Data format</h2>
                    <p>
                        The timestamps of the photometric data are converted in BJD<sub>TDB</sub>.
                    </p>
                </div>
            </div>
        </>
    )
}
