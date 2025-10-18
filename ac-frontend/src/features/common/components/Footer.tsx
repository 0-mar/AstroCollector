export default function Footer() {
    const date = new Date()
    const dateString = new Intl.DateTimeFormat("cs-CZ").format(date).toString()

    return (
        <footer className="footer footer-horizontal footer-center bg-secondary text-primary-content p-10">
            <div className="flex flex-row items-center gap-y-2">
                <img className={"w-15 h-15"}
                     src="/planet.svg"
                     alt="planet logo" />
                <span
                    className="self-center text-2xl font-semibold whitespace-nowrap text-transparent bg-clip-text bg-gradient-to-r to-black from-amber-400">
                    AstroCollector
                </span>
            </div>

            <p className="font-bold">

                <br/>
                Developed for the <a className={"text-blue-600 hover:underline"} href={"https://physics.muni.cz/en"} target={"_blank"}>Department of Physics, Faculty of Science, Masaryk University</a>
            </p>
            <p>Copyright © {new Date().getFullYear()} Ondřej Marek</p>
            <p>Last update: {dateString}</p>
        </footer>
    )
}
