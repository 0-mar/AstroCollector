import {useQuery} from "@tanstack/react-query";
import BaseApi from "@/features/common/api/baseApi.ts";
import type {Resources} from "@/features/catalogsOverview/types.ts";


const useCatalogPluginResources = (pluginId: string) => {
    return useQuery({
        queryKey: [`${pluginId}_resources`],
        queryFn: () => BaseApi.get<Resources>(`/plugins/resources/${pluginId}`)
    })
}

export default useCatalogPluginResources;
