import {ClientPaginatedDataTable} from "@/components/table/ClientPaginatedDataTable.tsx";
import {identifierColumns} from "@/components/table/Columns.tsx";
import type {Identifier} from "@/features/search/menu/types.ts";

type StellarObjectsTabProps = {
    identifiers: Identifier[]
}

const StellarObjectsTab = ({identifiers}: StellarObjectsTabProps) => {
    return (
        <>
            <span className={"font-bold"}>{identifiers.length}</span> stellar object{identifiers.length !== 1 ? "s" : ""} found
            <ClientPaginatedDataTable data={identifiers} columns={identifierColumns} defaultSorting={[{id: "distance", desc: false}]}/>
        </>
    )
}

export default StellarObjectsTab;
