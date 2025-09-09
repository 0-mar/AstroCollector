import {useContext, useEffect, useState} from "react";
import {SearchFormContext} from "@/components/search/form/SearchFormContext.tsx";
import ErrorAlert from "@/components/alerts/ErrorAlert.tsx";

const AladinCutout = () => {
    const searchFormContext = useContext(SearchFormContext)
    const [showError, setShowError] = useState(false)

    useEffect(() => {
        // TODO: NED as well?
        let declared;
        try {
            A;
            declared = true;
        } catch(e) {
            declared = false;
        }

        if (declared) {
            setShowError(false);
        } else {
            setShowError(true);
        }

        const target = searchFormContext?.searchValues.objectName ?? `${searchFormContext?.searchValues.rightAscension} ${searchFormContext?.searchValues.declination}`
        let aladin = A.aladin('#aladin-lite-div', { survey: 'P/DSS2/color', fov: 2 / 60, target: target})
        aladin.addCatalog(A.catalogFromSimbad(target, 2 / 60, {onClick: 'showTable'}));
        aladin.addCatalog(A.catalogFromNED(target, 2 / 60, {onClick: 'showPopup', shape: 'plus'}));
        aladin.setFov(2/60)
    }, [])

    if (showError) {
        return <ErrorAlert title={"Failed to load Aladin Lite"} description={"Aladin Lite is not available."} />
    }

    return (
        <div id='aladin-lite-div' style={{ width: '506px', height: '506px' }} />
    )
}

export default AladinCutout;
