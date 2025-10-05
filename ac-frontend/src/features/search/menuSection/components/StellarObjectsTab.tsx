import {ClientPaginatedDataTable} from "@/features/common/dataTable/ClientPaginatedDataTable.tsx";
import {identifierColumns} from "@/features/common/dataTable/Columns.tsx";
import type {Identifier} from "@/features/search/menuSection/types.ts";

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
