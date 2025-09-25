import { createFileRoute } from "@tanstack/react-router"
import {roleGuard} from "@/features/routing/roleGuard.ts";
import {UserRoleEnum} from "@/features/auth/types.ts";
import useCatalogPluginsQuery from "@/features/plugin/useCatalogs.ts";
import LoadingSkeleton from "@/components/loading/LoadingSkeleton.tsx";
import ErrorAlert from "@/components/alerts/ErrorAlert.tsx";
import {ClientPaginatedDataTable} from "@/components/table/ClientPaginatedDataTable.tsx";
import {catalogPluginsColumns} from "@/components/table/Columns.tsx";
import AddPluginDialog from "@/components/admin/AddPluginDialog.tsx";


export const Route = createFileRoute('/admin/catalogManagement')({
    beforeLoad: roleGuard([UserRoleEnum.SUPER_ADMIN]),
    component: CatalogPLuginsManagementComponent,
})


function CatalogPLuginsManagementComponent() {
    const catalogsQuery = useCatalogPluginsQuery();

    if (catalogsQuery.isPending) {
        return (
            <div className="p-8">
                <LoadingSkeleton text="Loading catalog plugins..." />
            </div>
        )
    }

    if (catalogsQuery.isError) {
        return (
            <div className="p-8">
                <ErrorAlert title="Failed to load catalog plugins" description={catalogsQuery.error?.message} />
            </div>
        )
    }

    return (
        <div className="flex flex-col gap-2 p-8">
            <header className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-bold">Manage catalog plugins</h1>
            </header>
            <div className={"me-auto"}>
                <AddPluginDialog/>
            </div>
            <ClientPaginatedDataTable data={catalogsQuery.data.data} columns={catalogPluginsColumns}/>
        </div>
    )
}
