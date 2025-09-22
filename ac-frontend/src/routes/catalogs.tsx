import {createFileRoute} from "@tanstack/react-router";
import useCatalogPluginsQuery from "@/features/plugin/useCatalogs.ts";
import LoadingSkeleton from "@/components/loading/LoadingSkeleton.tsx";
import ErrorAlert from "@/components/alerts/ErrorAlert.tsx";
import CatalogCard from "@/components/catalogsOverview/CatalogCard.tsx";
import InfoAlert from "@/components/alerts/InfoAlert.tsx";
import {MapPinCheckInside} from "lucide-react";

export const Route = createFileRoute('/catalogs')({
    component: CatalogsComponent,
})

function CatalogsComponent(){
    const catalogsQuery = useCatalogPluginsQuery();

    return (
        <div className={"bg-blue-100"}>
            <div className={"flex flex-col p-8 gap-y-2"}>
                {
                    catalogsQuery.isPending ? (
                        <LoadingSkeleton text="Loading catalogs..." />
                    ) : catalogsQuery.isError ? (
                        <ErrorAlert
                            title="Failed to load catalogs"
                            description={catalogsQuery.error?.message}
                        />
                    ) : (
                        <>
                            <h1 className="text-3xl font-extrabold">Supported catalogs</h1>
                            <span className="inline-flex items-center gap-1">
                                <MapPinCheckInside/>
                                = catalog groups stellar objects by identificator
                            </span>
                            {catalogsQuery.data.data.map((catalogDto) => (
                                <CatalogCard
                                    key={catalogDto.id ?? catalogDto.name}
                                    catalogData={catalogDto}
                                />
                            ))}

                            {catalogsQuery.data.data.length === 0 && (
                                <InfoAlert title="No catalogs found">
                                    <p>Please contact the administrators</p>
                                </InfoAlert>
                            )}
                        </>
                    )
                }
            </div>
        </div>
    )
}
