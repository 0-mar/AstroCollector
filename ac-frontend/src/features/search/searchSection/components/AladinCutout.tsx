import {useContext, useEffect, useRef, useState} from "react";
import ErrorAlert from "@/features/common/alerts/ErrorAlert.tsx";
import LoadingSkeleton from "@/features/common/loading/LoadingSkeleton.tsx";
import {ResolvedObjectCoordsContext} from "@/features/search/searchSection/components/ResolvedObjectCoordsProvider.tsx";

type AladinCutoutProps = {
    loaded: boolean
}

const AladinCutout = ({loaded}: AladinCutoutProps) => {
    const resolvedObjectCoordsContext = useContext(ResolvedObjectCoordsContext)
    const containerRef = useRef<HTMLDivElement | null>(null);
    const aladinRef = useRef<any>(null);
    const [showError, setShowError] = useState(false);

    useEffect(() => {
        if (!loaded || resolvedObjectCoordsContext?.resolvedObjectCoords === null) {
            return;
        }

        const aladinGlobal = (globalThis as any).A;
        if (!containerRef.current || !aladinGlobal) {
            setShowError(true);
            return;
        }
        setShowError(false)

        const target = `${resolvedObjectCoordsContext?.resolvedObjectCoords?.rightAscension} ${resolvedObjectCoordsContext?.resolvedObjectCoords?.declination}`

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
    }, [loaded, resolvedObjectCoordsContext?.resolvedObjectCoords]);

    useEffect(() => {
        const aladinGlobal = (globalThis as any).A;
        const aladin = aladinRef.current;
        if (!aladinGlobal || !aladin || resolvedObjectCoordsContext?.resolvedObjectCoords === null) {
            return;
        }

        const target = `${resolvedObjectCoordsContext?.resolvedObjectCoords?.rightAscension} ${resolvedObjectCoordsContext?.resolvedObjectCoords?.declination}`

        aladin.gotoObject(target);
        aladin.setFov(2/60);

        aladin.addCatalog(aladinGlobal.catalogFromSimbad(target, 2 / 60, {onClick: 'showPopup'}));
        aladin.addCatalog(aladinGlobal.catalogFromNED(target, 2 / 60, {onClick: 'showPopup', shape: 'plus'}));
    }, [resolvedObjectCoordsContext?.resolvedObjectCoords])

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
