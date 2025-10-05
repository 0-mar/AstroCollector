export type PaginationResponse<T> = {
  data: Array<T>;
  count: number;
  total_items: number;
};

export type SubmitTaskDto = {
    task_id: string;
}

export enum TaskStatus {
    IN_PROGRESS = "IN_PROGRESS",
    COMPLETED = "COMPLETED",
    FAILED = "FAILED",
}

export type TaskStatusDto = {
    task_id: string;
    status: TaskStatus;
}
