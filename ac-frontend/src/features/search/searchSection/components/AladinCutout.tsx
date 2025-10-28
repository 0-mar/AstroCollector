import {useContext, useEffect, useRef, useState} from "react";
import {SearchFormContext} from "@/features/search/searchSection/components/SearchFormContext.tsx";
import ErrorAlert from "@/features/common/alerts/ErrorAlert.tsx";
import LoadingSkeleton from "@/features/common/loading/LoadingSkeleton.tsx";

type AladinCutoutProps = {
    loaded: boolean
}

const AladinCutout = ({loaded}: AladinCutoutProps) => {
    const searchFormContext = useContext(SearchFormContext)
    const containerRef = useRef<HTMLDivElement | null>(null);
    const aladinRef = useRef<any>(null);
    const [showError, setShowError] = useState(false);

    useEffect(() => {
        if (!loaded) {
            return;
        }

        const aladinGlobal = (globalThis as any).A;
        if (!containerRef.current || !aladinGlobal) {
            setShowError(true);
            return;
        }
        setShowError(false)

        const target = searchFormContext?.searchValues.objectName != "" ? searchFormContext?.searchValues.objectName :
            `${searchFormContext?.searchValues.rightAscension} ${searchFormContext?.searchValues.declination}`

        const aladin = aladinGlobal.aladin(containerRef.current,
            { survey: 'P/DSS2/color', fov: 2 / 60, target: target});
        aladinRef.current = aladin;

        aladin.addCatalog(aladinGlobal.catalogFromSimbad(target, 2 / 60, {onClick: 'showPopup'}));
        aladin.addCatalog(aladinGlobal.catalogFromNED(target, 2 / 60, {onClick: 'showPopup', shape: 'plus'}));
        aladin.setFov(2/60)

        // cleanup
        return () => {
            try {
                aladinRef.current = null;
                if (containerRef.current) containerRef.current.innerHTML = "";
            } catch {}
        };
    }, [loaded]);

    useEffect(() => {
        const aladinGlobal = (globalThis as any).A;
        const aladin = aladinRef.current;
        if (!aladinGlobal || !aladin) {
            return;
        }

        console.log(searchFormContext?.searchValues)
        const target = searchFormContext?.searchValues.objectName != "" ? searchFormContext?.searchValues.objectName :
            `${searchFormContext?.searchValues.rightAscension} ${searchFormContext?.searchValues.declination}`

        aladin.gotoObject(target);
        aladin.setFov(2/60);

        aladin.addCatalog(aladinGlobal.catalogFromSimbad(target, 2 / 60, {onClick: 'showPopup'}));
        aladin.addCatalog(aladinGlobal.catalogFromNED(target, 2 / 60, {onClick: 'showPopup', shape: 'plus'}));
    }, [searchFormContext?.searchValues])

    if (showError) {
        return <ErrorAlert title={"Failed to load Aladin Lite"} description={"Aladin Lite is not available."} />
    }

    if (!loaded) {
        return <LoadingSkeleton text={"Loading Aladin..."} />
    }

    return (
        <div ref={containerRef} style={{ width: '506px', height: '506px' }} />
    )
}

export default AladinCutout;
