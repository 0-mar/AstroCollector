import {MapPinCheckInside} from "lucide-react";
import type {PluginDto} from "@/features/catalogsOverview/types.ts";

type CatalogCardProps = {
    catalogData: PluginDto
}

const CatalogCard = ({catalogData}: CatalogCardProps) => {
    return (
        <div className={"flex flex-col p-4 bg-white rounded-md shadow-md border-black border-1 gap-y-2"}>
            <h2 className="text-2xl font-medium">
                <span className="inline-flex items-center gap-1">
                    {catalogData.name}{catalogData.directly_identifies_objects && <MapPinCheckInside/>}
                </span>
            </h2>
            <p>{catalogData.description}</p>
            <a className={"me-auto text-white bg-blue-700 hover:bg-blue-800  font-medium rounded-lg text-sm px-5 py-2.5"} href={catalogData.catalog_url} target={"_blank"}>Catalog website</a>
        </div>
    )
}

export default CatalogCard;
