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
import {useMemo, useState} from "react";
import type {PhotometricDataDto} from "@/features/search/lightcurve/types.ts";
import {DataTablePagination} from "@/components/table/DataTablePagination.tsx";
import {useQuery} from "@tanstack/react-query";
import BaseApi from "@/features/api/baseApi.ts";
import {type PaginationResponse} from "@/features/api/types.ts";
import {keepPreviousData} from "@tanstack/query-core";

const photometricColumns: ColumnDef<PhotometricDataDto>[] = [
    {
        accessorKey: "julian_date",
        header: "Julian Date",
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
}

function PhotometricDataTable({taskIds}: PhotometricDataTableProps) {
    const {count, setPagination, offset, pagination} = usePagination();

    const photometricResultsQuery = useQuery({
        queryKey: [`photometric_data_page`, pagination, taskIds],
        queryFn: () => {
            return BaseApi.post<PaginationResponse<PhotometricDataDto>>(`/retrieve/photometric-data`, {task_id__in: taskIds, offset: offset, count: count})
        },
        refetchInterval: (query) => {
            const data = query.state.data;
            if (!data) {
                return 1000;
            }
            return data.count > 0 ? false : 1000;
        },
        placeholderData: keepPreviousData
    });

    const defaultData = useMemo(() => [], [])

    const table = useReactTable<PhotometricDataDto>({
        data: photometricResultsQuery.data?.data ?? defaultData,
        columns: photometricColumns,
        getCoreRowModel: getCoreRowModel(),
        manualPagination: true,
        rowCount: photometricResultsQuery.data?.total_items,

        state: { pagination },
        onPaginationChange: setPagination,
    })
    console.log(taskIds)
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
