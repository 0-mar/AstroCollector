import {useContext} from "react";
import {RangeContext} from "@/components/search/lightcurve/CurrentRangeContext.tsx";

const VisibleRange = () => {
    const rangeContext = useContext(RangeContext)


    return (
        <div>
            <h2>Visible plot range</h2>
            <h3>From: {rangeContext?.currMinRange ?? "start"} MJD</h3>
            <h3>To: {rangeContext?.currMaxRange ?? "end"} MJD</h3>
        </div>
    )
}

export default VisibleRange;
