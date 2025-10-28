import {useQuery} from "@tanstack/react-query";
import BaseApi from "@/features/common/api/baseApi.ts";
import LoadingSkeleton from "@/features/common/loading/LoadingSkeleton.tsx";
import ErrorAlert from "@/features/common/alerts/ErrorAlert.tsx";
import SuccessAlert from "@/features/common/alerts/SuccessAlert.tsx";
import type {ResolvedCoordsDto} from "@/features/search/searchSection/types.ts";
import {useContext, useEffect} from "react";
import {ObjectCoordsContext} from "@/features/search/searchSection/components/ObjectCoordsProvider.tsx";
import {SearchFormContext} from "@/features/search/searchSection/components/SearchFormContext.tsx";


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
