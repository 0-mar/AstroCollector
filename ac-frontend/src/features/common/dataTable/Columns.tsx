import type {ColumnDef} from "@tanstack/react-table"
import IdentifierCheckbox from "@/features/search/menuSection/components/IdentifierCheckbox.tsx";
import {Button} from "../../../../components/ui/button.tsx";
import {ArrowUpDown} from "lucide-react";
import DownloadPluginSrcButton from "@/features/admin/components/DownloadPluginSrcButton.tsx";
import EditPluginDialog from "@/features/admin/components/EditPluginDialog.tsx";
import DeletePluginDialog from "@/features/admin/components/DeletePluginDialog.tsx";
import type {Identifier} from "@/features/search/menuSection/types.ts";
import type {PluginDto} from "@/features/catalogsOverview/types.ts";


export const identifierColumns: ColumnDef<Identifier>[] = [
    {
        header: "Select",
        cell: ({ row }) => {
            const { id, identifier } = row.original;
            return (
                <IdentifierCheckbox id={id} identifier={identifier}/>
            )
        },
        enableSorting: false
    },
    {
        accessorKey: "identifier.name",
        header: "Name",
    },
    {
        accessorKey: "identifier.ra_deg",
        header: "Right ascension (deg)",
    },
    {
        accessorKey: "identifier.dec_deg",
        header: "Declination (deg)",
    },
    {
        id: "distance",
        accessorKey: "identifier.dist_arcsec",
        header: ({ column }) => {
            return (
                <Button
                    variant="ghost"
                    onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
                >
                    Distance (arcsec)
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                </Button>
            )
        },
    },
]


export const catalogPluginsColumns: ColumnDef<PluginDto>[] = [
    {
        accessorKey: "name",
        header: "Name",
    },
    {
        header: "Created",
        cell: ({ row }) => {
            const date = new Date(row.original.created);

            return (
                <p>
                    {date.toLocaleString()}
                </p>
            )
        },
        enableSorting: false
    },
    {
        header: "Download source code",
        cell: ({ row }) => {
            return (
                <DownloadPluginSrcButton pluginDto={row.original}/>
            )
        },
        enableSorting: false
    },
    {
        header: "Edit catalog plugin",
        cell: ({ row }) => {
            return (
                <EditPluginDialog pluginDto={row.original}/>
            )
        },
        enableSorting: false
    },
    {
        header: "Delete catalog plugin",
        cell: ({ row }) => {
            return (
                <DeletePluginDialog pluginDto={row.original}/>
            )
        },
        enableSorting: false
    },
]
