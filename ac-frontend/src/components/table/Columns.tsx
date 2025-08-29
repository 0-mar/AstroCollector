import type {ColumnDef} from "@tanstack/react-table"
import type {Identifier} from "@/features/search/types.ts";
import type {PhotometricDataDto} from "@/features/search/lightcurve/types.ts";
import IdentifierCheckbox from "@/components/search/menu/IdentifierCheckbox.tsx";


export const identifierColumns: ColumnDef<Identifier>[] = [
    {
        header: "Select",
        cell: ({ row }) => {
            const { id, identifier } = row.original;
            return (
                <IdentifierCheckbox id={id} identifier={identifier}/>
            )
        },
    },
    {
        accessorKey: "identifier.ra_deg",
        header: "Right ascension (deg)",
    },
    {
        accessorKey: "identifier.dec_deg",
        header: "Declination (deg)",
    },
]
