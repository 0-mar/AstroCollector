import {useQuery} from "@tanstack/react-query";
import BaseApi from "@/features/api/baseApi.ts";
import type {PaginationResponse} from "@/features/api/types.ts";

import type {PluginDto} from "@/features/plugin/types.ts";

const useCatalogPluginsQuery = () => {
    return useQuery({
        queryKey: ['plugins'],
        queryFn: () => BaseApi.post<PaginationResponse<PluginDto>>('/plugins/list', {}, {params: {
                offset: 0,
                count: 1000
            }}),
    })
}

export default useCatalogPluginsQuery;
