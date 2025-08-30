import {useQuery} from "@tanstack/react-query";
import BaseApi from "@/features/api/baseApi.ts";
import LoadingSkeleton from "@/components/loading/LoadingSkeleton.tsx";
import ErrorAlert from "@/components/alerts/ErrorAlert.tsx";
import SuccessAlert from "@/components/alerts/SuccessAlert.tsx";
import type {ResolvedCoordsDto} from "@/features/nameResolving/types.ts";

type CoordsPanelProps = {
    objectName: string,
}

const CoordsPanel = ({objectName}: CoordsPanelProps) => {
    const coordsQuery = useQuery({
        queryKey: ['coords', objectName],
        queryFn: () => BaseApi.post<ResolvedCoordsDto>('/so-name-resolve', {name: objectName}),
    })

    if (coordsQuery.isPending) {
        return <LoadingSkeleton text={"Resolving coordinates..."} />
    }

    if (coordsQuery.isError) {
        return <ErrorAlert title={"Failed to resolve coordinates"} description={coordsQuery.error.message} />
    }

    return (
        <SuccessAlert description={`'${objectName}' was resolved to: ${coordsQuery.data.ra_deg} ${coordsQuery.data.dec_deg}`} title={"Successfully resolved coordinates"} />
    )
}

export default CoordsPanel;
