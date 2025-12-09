import type {PhotometricDataDto} from "@/features/search/photometricDataSection/types.ts";
import {useInfiniteQuery} from "@tanstack/react-query";
import {useEffect} from "react";
import BaseApi from "@/features/common/api/baseApi.ts";
import type {PaginationResponse} from "@/features/common/api/types.ts";

type PhotometryDataLoader = {
    taskId: string;
    onData: (rows: PhotometricDataDto[]) => void,
}

const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));
const COUNT = 5000;

/**
 * PhotometricDataLoader is a headless React functional component that retrieves photometric data
 * for a given task ID.
 */
const PhotometricDataLoader = ({ taskId, onData }: PhotometryDataLoader) => {
    const q = useInfiniteQuery({
        queryKey: ['pd', taskId],
        initialPageParam: 0,
        queryFn: ({ pageParam }) =>
            BaseApi.post<PaginationResponse<PhotometricDataDto>>(
                `/retrieve/photometric-data?offset=${pageParam}&count=${COUNT}`,
                { filters: {task_id__eq: taskId} }
            ),
        getNextPageParam: (lastPage, pages) => {
            const offset = pages.reduce((n, p) => n + p.count, 0);
            return offset < lastPage.total_items ? offset : undefined;
        },
        staleTime: Infinity,
    });

    // download all data
    useEffect(() => {
        if (!q.hasNextPage || q.isFetchingNextPage) {
            return;
        }
        sleep(500).then(() => q.fetchNextPage());
    }, [q.hasNextPage, q.isFetchingNextPage]);

    // merge data
    useEffect(() => {
        if (!q.hasNextPage) {
            const rows = q.data?.pages.flatMap(p => p.data) ?? [];
            if (rows.length === 0) {
                return;
            }
            onData(rows);
        }
    }, [q.dataUpdatedAt]);

    return null;
}

export default PhotometricDataLoader
