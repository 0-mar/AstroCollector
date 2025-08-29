import {
    type ColumnDef,
    flexRender, getCoreRowModel,
    useReactTable,
} from "@tanstack/react-table"

import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/../components/ui/table"
import {useEffect, useMemo, useState} from "react";
import type {PhotometricDataDto} from "@/features/search/lightcurve/types.ts";
import {DataTablePagination} from "@/components/table/DataTablePagination.tsx";
import {useQueries, useQuery} from "@tanstack/react-query";
import BaseApi from "@/features/api/baseApi.ts";
import {type PaginationResponse, TaskStatus} from "@/features/api/types.ts";
import type {Identifier} from "@/features/search/types.ts";
import type {Identifiers} from "@/features/search/menu/types.ts";
import {keepPreviousData} from "@tanstack/query-core";

const photometricColumns: ColumnDef<PhotometricDataDto>[] = [
    {
        accessorKey: "julian_date",
        header: "Modified Julian Date",
    },
    {
        accessorKey: "magnitude",
        header: "Magnitude",
    },
    {
        accessorKey: "magnitude_error",
        header: "Magnitude Error",
    },
    {
        accessorKey: "light_filter",
        header: "Light Filter",
    },
]

export function usePagination() {
    const [pagination, setPagination] = useState({
        pageSize: 10,
        pageIndex: 0,
    });
    const {pageSize, pageIndex} = pagination;

    return {
        count: pageSize,
        setPagination,
        pagination,
        offset: pageSize * pageIndex,
    };
}

type PhotometricDataTableProps = {
    taskIds: string[],
    taskStatusQueries,
    currentObjectIdentifiers: Identifiers
}

function PhotometricDataTable({taskIds, taskStatusQueries, currentObjectIdentifiers}: PhotometricDataTableProps) {

    // const resultQueries = useQueries({
    //     queries: Object.values(currentObjectIdentifiers).map((identifier, idx) => {
    //         return {
    //             queryKey: [`lcData_${identifier.plugin_id}_${identifier.ra_deg}_${identifier.dec_deg}`],
    //             queryFn: () => BaseApi.post<PaginationResponse<PhotometricDataDto>>(`/retrieve/photometric-data/${lightcurveTaskQueries[idx].data?.task_id}`, {task_id: lightcurveTaskQueries[idx].data?.task_id}),
    //             enabled: taskStatusQueries[idx].data?.status === TaskStatus.COMPLETED,
    //             staleTime: Infinity
    //         }
    //     }),
    // })



    const {count, setPagination, offset, pagination} = usePagination();
    const [curTaskIdIdx, setCurTaskIdIdx] = useState(0)

    const photometricResultsQuery = useQuery({
        queryKey: [`photometric_data_page`, pagination],
        queryFn: () => {
            // get task ID. The ID will be ALWAYS present, since the query starts only when the taskQuery was successful
            return BaseApi.post<PaginationResponse<PhotometricDataDto>>(`/retrieve/photometric-data`, {task_id__in: taskIds, offset: offset, count: count})
        },
        placeholderData: keepPreviousData
        // enabled: taskStatusQuery.data?.status === TaskStatus.COMPLETED,
        // staleTime: Infinity
    });

    useEffect(() => {
        if (photometricResultsQuery.data?.count == 0) {
            setCurTaskIdIdx(curTaskIdIdx + 1)
        }
    }, [photometricResultsQuery.data?.data]);
    photometricResultsQuery.data?.data;

    const defaultData = useMemo(() => [], [])

    const table = useReactTable<PhotometricDataDto>({
        data: photometricResultsQuery.data?.data ?? defaultData,
        columns: photometricColumns,
        getCoreRowModel: getCoreRowModel(),
        manualPagination: true,
        //rowCount: total,
        rowCount: photometricResultsQuery.data?.total_items,

        // v8 style: keep pagination in the `state` object
        state: { pagination },
        onPaginationChange: setPagination,
        // optional but common: provide pageCount when doing manual pagination
        // pageCount: Math.ceil(total / pagination.pageSize),
    })

    return (
        <div>
            <div className="overflow-hidden rounded-md border">
                <Table>
                    <TableHeader>
                        {table.getHeaderGroups().map((headerGroup) => (
                            <TableRow key={headerGroup.id}>
                                {headerGroup.headers.map((header) => {
                                    return (
                                        <TableHead key={header.id}>
                                            {header.isPlaceholder
                                                ? null
                                                : flexRender(
                                                    header.column.columnDef.header,
                                                    header.getContext()
                                                )}
                                        </TableHead>
                                    )
                                })}
                            </TableRow>
                        ))}
                    </TableHeader>
                    <TableBody>
                        {table.getRowModel().rows?.length ? (
                            table.getRowModel().rows.map((row) => (
                                <TableRow
                                    key={row.id}
                                    data-state={row.getIsSelected() && "selected"}
                                >
                                    {row.getVisibleCells().map((cell) => (
                                        <TableCell key={cell.id}>
                                            {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                        </TableCell>
                                    ))}
                                </TableRow>
                            ))
                        ) : (
                            <TableRow>
                                <TableCell colSpan={photometricColumns.length} className="h-24 text-center">
                                    No results.
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </div>
            <DataTablePagination table={table}/>
        </div>
    )
}

export default PhotometricDataTable;
