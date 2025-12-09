import {useContext, useEffect, useRef, useState} from "react";
import ErrorAlert from "@/features/common/alerts/ErrorAlert.tsx";
import LoadingSkeleton from "@/features/common/loading/LoadingSkeleton.tsx";
import {ResolvedObjectCoordsContext} from "@/features/search/searchSection/components/ResolvedObjectCoordsProvider.tsx";

type AladinCutoutProps = {
    loaded: boolean
}

/**
 * A React functional component that integrates and renders the Aladin Lite sky atlas.
 * Displays the map based on the resolved object coordinates provided.
 */
const AladinCutout = ({loaded}: AladinCutoutProps) => {
    const resolvedObjectCoordsContext = useContext(ResolvedObjectCoordsContext);
    // the container, where aladin lives
    const containerRef = useRef<HTMLDivElement | null>(null);
    // reference to aladin instance. We do not want to rerender each time a star is search, so it is as a ref
    const aladinRef = useRef<any>(null);
    const [showError, setShowError] = useState(false);

    useEffect(() => {
        if (!loaded || !resolvedObjectCoordsContext?.resolvedObjectCoords || !containerRef.current) {
            return;
        }

        const aladinGlobal = (globalThis as any).A;
        if (!aladinGlobal) {
            setShowError(true);
            return;
        }

        let aladin;
        const target = `${resolvedObjectCoordsContext?.resolvedObjectCoords?.rightAscension} ${resolvedObjectCoordsContext?.resolvedObjectCoords?.declination}`

        if (!aladinRef.current) {
            // create aladin for the first time
            aladin = aladinGlobal.aladin(containerRef.current,
                { survey: 'P/DSS2/color', fov: 2 / 60, target: target});
            aladin.addCatalog(aladinGlobal.catalogFromSimbad(target, 2 / 60, {onClick: 'showPopup'}));
            aladin.addCatalog(aladinGlobal.catalogFromNED(target, 2 / 60, {onClick: 'showPopup', shape: 'plus'}));
            aladinRef.current = aladin;
        } else {
            // change target
            aladin = aladinRef.current;
            aladin.gotoObject(target);
        }

        aladin.setFov(2/60);
    }, [loaded, resolvedObjectCoordsContext?.resolvedObjectCoords]);

    if (showError) {
        return <ErrorAlert title={"Failed to load Aladin Lite"} description={"Aladin Lite is not available."} />
    }

    if (!loaded || !resolvedObjectCoordsContext?.resolvedObjectCoords) {
        return <LoadingSkeleton text={"Loading Aladin..."} />
    }

    return (
        <div ref={containerRef} style={{ width: '506px', height: '506px' }} />
    )
}

export default AladinCutout;
