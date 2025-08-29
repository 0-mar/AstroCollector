import {createFileRoute} from '@tanstack/react-router'
import {identifierColumns} from "@/components/table/Columns.tsx";
import type {Identifier} from "@/features/search/types.ts";
import {ClientPaginatedDataTable} from "@/components/table/ClientPaginatedDataTable.tsx";
import {IdentifiersProvider} from "@/components/search/menu/IdentifiersContext.tsx";

export const Route = createFileRoute('/test/')({
    component: Test,
})

function Test() {
    const data: Array<Identifier> = []
    for (let i = 0; i < 1000; i++) {
        data.push({
            id: "gfsdgfsd",
            task_id: "fdsgtrsgfxd",
            identifier: {
                plugin_id: "fdsfsdgfds",
                dec_deg: 245.74,
                ra_deg: 32.451
            }
        })
    }


    return (
        <div className="container mx-auto py-10">
            <IdentifiersProvider>
                <ClientPaginatedDataTable data={data} columns={identifierColumns}/>
            </IdentifiersProvider>
        </div>
    )
}
