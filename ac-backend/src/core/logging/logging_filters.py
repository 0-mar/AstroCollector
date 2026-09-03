import logging


class TaskStatusPollFilter(logging.Filter):
    path_prefix = "/api/tasks/task_status/"

    def filter(self, record):
        # the uvicorn.access message format: '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s'
        # found at https://uvicorn.dev/concepts/logging/#default-configuration
        if record.name != "uvicorn.access":
            return True

        try:
            _client, _method, path, _protocol, status = record.args
            return not (str(path).startswith(self.path_prefix) and int(status) < 400)
        except (TypeError, ValueError):
            # If Uvicorn changes its log structure, don't break the request.
            return True
