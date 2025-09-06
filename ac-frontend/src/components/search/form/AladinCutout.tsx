import {useContext, useEffect} from "react";
import {SearchFormContext} from "@/components/search/form/SearchFormContext.tsx";

const AladinCutout = () => {
    const searchFormContext = useContext(SearchFormContext)

    useEffect(() => {
        let aladin = A.aladin('#aladin-lite-div', { survey: 'P/DSS2/color', fov:60, target:  searchFormContext?.searchValues.objectName ?? `${searchFormContext?.searchValues.rightAscension} ${searchFormContext?.searchValues.declination}`})
        //aladin.setFov(1)
    }, [])

    return (
        <div id='aladin-lite-div' style={{ width: '100%', height: '100%' }} />
    )
}

export default AladinCutout;
