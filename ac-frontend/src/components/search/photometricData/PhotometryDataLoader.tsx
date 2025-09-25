import type {PhotometricDataDto} from "@/features/search/photometricDataSection/types.ts";
import {useInfiniteQuery} from "@tanstack/react-query";
import BaseApi from "@/features/api/baseApi.ts";
import type {PaginationResponse} from "@/features/api/types.ts";
import {useEffect} from "react";

type PhotometryDataLoader = {
    taskId: string;
    onData: (rows: PhotometricDataDto[]) => void
}

const PhotometryDataLoader = ({ taskId, onData }: PhotometryDataLoader) => {
    const COUNT = 5000;
    const q = useInfiniteQuery({
        queryKey: ['pd', taskId],
        initialPageParam: 0,
        queryFn: ({ pageParam }) =>
            BaseApi.post<PaginationResponse<PhotometricDataDto>>(
                `/retrieve/photometric-data?offset=${pageParam}&count=${COUNT}`,
                { task_id__eq: taskId }
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
        q.fetchNextPage();
    }, [q.hasNextPage, q.isFetchingNextPage]);

    // merge data
    useEffect(() => {
        const rows = q.data?.pages.flatMap(p => p.data) ?? [];
        onData(rows);
    }, [q.dataUpdatedAt]);

    return null;
}

export default PhotometryDataLoader
