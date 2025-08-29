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
import {Button} from "../../../components/ui/button.tsx";
import {useState} from "react";
import type {PhotometricDataDto} from "@/features/search/lightcurve/types.ts";

interface DataTableProps {
    columns: ColumnDef<PhotometricDataDto>[]
}


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

function useFakeAPI(path: string, {pagination}: { pagination: { offset: number, count: number } }) {
    const lightCurveData: Array<PhotometricDataDto> = []
    for (let i = 0; i < 1000; i++) {
        lightCurveData.push({
            julian_date: i,
            magnitude: i,
            magnitude_error: i,
            plugin_id: "fdsfsd451",
            light_filter: i % 2 === 0 ? 'u' : 'g'
        })
    }
    return {
        data: lightCurveData.slice(pagination.offset, pagination.offset + pagination.count),
        total: 1000,
        loading: false
    };
}


export function PhotometricDataTable({
                              columns,
                          }: DataTableProps) {

    const {count, setPagination, offset, pagination} = usePagination();

    const {data, total, loading} = useFakeAPI("/episodes",
        {pagination: {offset, count}}
    );

    const table = useReactTable<PhotometricDataDto>({
        data,
        columns,                       // now matches ColumnDef<PhotometricDataDto>[]
        getCoreRowModel: getCoreRowModel(),
        manualPagination: true,
        rowCount: total,

        // v8 style: keep pagination in the `state` object
        state: { pagination },
        onPaginationChange: setPagination,
        // optional but common: provide pageCount when doing manual pagination
        pageCount: Math.ceil(total / pagination.pageSize),
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
                                <TableCell colSpan={columns.length} className="h-24 text-center">
                                    No results.
                                </TableCell>
                            </TableRow>
                        )}
                    </TableBody>
                </Table>
            </div>
            <div className="flex items-center justify-end space-x-2 py-4">
                <Button
                    variant="outline"
                    size="sm"
                    onClick={() => table.previousPage()}
                    disabled={!table.getCanPreviousPage()}
                >
                    Previous
                </Button>
                <Button
                    variant="outline"
                    size="sm"
                    onClick={() => table.nextPage()}
                    disabled={!table.getCanNextPage()}
                >
                    Next
                </Button>
                <Button
                    onClick={() => table.firstPage()}
                    disabled={!table.getCanPreviousPage()}
                >
                    {'<<'}
                </Button>
                <Button
                    onClick={() => table.previousPage()}
                    disabled={!table.getCanPreviousPage()}
                >
                    {'<'}
                </Button>
                <Button
                    onClick={() => table.nextPage()}
                    disabled={!table.getCanNextPage()}
                >
                    {'>'}
                </Button>
                <Button
                    onClick={() => table.lastPage()}
                    disabled={!table.getCanNextPage()}
                >
                    {'>>'}
                </Button>

            </div>
        </div>
    )
}
