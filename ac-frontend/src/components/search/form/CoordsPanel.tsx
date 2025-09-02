import {useQuery} from "@tanstack/react-query";
import BaseApi from "@/features/api/baseApi.ts";
import LoadingSkeleton from "@/components/loading/LoadingSkeleton.tsx";
import ErrorAlert from "@/components/alerts/ErrorAlert.tsx";
import SuccessAlert from "@/components/alerts/SuccessAlert.tsx";
import type {ResolvedCoordsDto} from "@/features/nameResolving/types.ts";
import {useContext, useEffect} from "react";
import {ObjectCoordsContext} from "@/components/search/form/ObjectCoordsProvider.tsx";
import {SearchFormContext} from "@/components/search/form/SearchFormContext.tsx";


const CoordsPanel = () => {
    const objectCoordsContext = useContext(ObjectCoordsContext)
    const searchFormContext = useContext(SearchFormContext)

    const coordsQuery = useQuery({
        queryKey: ['coords', searchFormContext?.searchValues.objectName],
        queryFn: () => BaseApi.post<ResolvedCoordsDto>('/so-name-resolve', {name: searchFormContext?.searchValues.objectName}),
    })

    useEffect(() => {
        if (coordsQuery.isSuccess) {
            const next = { rightAscension: coordsQuery.data.ra_deg, declination: coordsQuery.data.dec_deg };
            objectCoordsContext?.setObjectCoords(prev =>
                (prev?.rightAscension === next.rightAscension && prev?.declination === next.declination)
                    ? prev
                    : next
            );
        }
    }, [coordsQuery.isSuccess, coordsQuery.data?.ra_deg, coordsQuery.data?.dec_deg])

    if (coordsQuery.isPending) {
        return <LoadingSkeleton text={"Resolving coordinates..."} />
    }

    if (coordsQuery.isError) {
        return <ErrorAlert title={"Failed to resolve coordinates"} description={coordsQuery.error.message} />
    }

    return (
        <SuccessAlert description={`'${searchFormContext?.searchValues.objectName}' was resolved to: ${coordsQuery.data.ra_deg} ${coordsQuery.data.dec_deg}`} title={"Successfully resolved coordinates"} />
    )
}

export default CoordsPanel;
