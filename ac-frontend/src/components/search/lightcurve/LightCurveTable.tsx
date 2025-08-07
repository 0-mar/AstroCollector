import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/../components/ui/table"
import type {PhotometricDataDto} from "@/features/search/lightcurve/types.ts";
import * as React from "react";

type LightCurveTableProps = {
    lightCurveData: PhotometricDataDto[]
}

const LightCurveTable = ({lightCurveData}: LightCurveTableProps) => {
    return (
        <Table>
            <TableHeader>
                <TableRow>
                    <TableHead>Julian Date</TableHead>
                    <TableHead>Magnitude</TableHead>
                    <TableHead>Magnitude error</TableHead>
                    <TableHead>Light filter</TableHead>
                </TableRow>
            </TableHeader>
            <TableBody>
                {lightCurveData.map((lcData) =>
                    <TableRow>
                        <TableCell>{lcData.julian_date}</TableCell>
                        <TableCell>{lcData.magnitude}</TableCell>
                        <TableCell>{lcData.magnitude_error}</TableCell>
                        <TableCell>{lcData.light_filter === null ? '' : lcData.light_filter}</TableCell>
                    </TableRow>
                )}
            </TableBody>
        </Table>
    );
}

// prevent the plot from rerendering, when the data has not changed
export default React.memo(LightCurveTable);
