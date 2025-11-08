import {useMemo, useState} from "react";
import type {Phase} from "@/features/catalogsOverview/types.ts";

const SOURCE_WEIGHT = 0.15;
const RESOURCES_WEIGHT = 0.85;

const useProgress = () => {
    // progress & phase state
    const [phase, setPhase] = useState<Phase>("idle");
    const [sourceProgress, setSourceProgress] = useState(0);     // 0..100
    const [resourcesProgress, setResourcesProgress] = useState(0); // 0..100

    // derived overall progress
    const overallProgress = useMemo(() => Math.round(
        SOURCE_WEIGHT * sourceProgress + RESOURCES_WEIGHT * resourcesProgress
    ), [sourceProgress, resourcesProgress]);

    return {
        phase,
        setPhase,
        setSourceProgress,
        setResourcesProgress,
        overallProgress,
    }
}

export default useProgress;
