import type {ColumnDef} from "@tanstack/react-table"
import type {Identifier} from "@/features/search/types.ts";
import IdentifierCheckbox from "@/components/search/menu/IdentifierCheckbox.tsx";
import {Button} from "../../../components/ui/button.tsx";
import {ArrowUpDown} from "lucide-react";


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
