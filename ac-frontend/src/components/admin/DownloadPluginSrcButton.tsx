import {useMutation} from "@tanstack/react-query";
import {toast} from "sonner";
import BaseApi from "@/features/api/baseApi.ts";
import {Button} from "../../../components/ui/button.tsx";
import {Download} from "lucide-react";

import type {PluginDto} from "@/features/plugin/types.ts";

type DownloadPluginSrcButtonProps = {
    pluginDto: PluginDto
}

const DownloadPluginSrcButton = ({pluginDto}: DownloadPluginSrcButtonProps) => {
    const downloadMutation = useMutation({
        onError: (_error) => {
            toast.error("Failed to download plugin source code.")
        },
        mutationFn: () => {
            return BaseApi.getBlob(`/plugins/download/${pluginDto.id}`)
        },
        onSuccess: ({blob}) => {
            const link = document.createElement("a");
            link.download = `plugin.py`;
            link.href = URL.createObjectURL(blob);
            link.click();
            URL.revokeObjectURL(link.href);
        },
        retry: (failureCount) => {
            return failureCount < 3;
        },
        retryDelay: (failureCount) => {
            return Math.min(1000 * 2 ** failureCount, 30000);
        },
    })

    return (
        <Button disabled={pluginDto.file_name === null} onClick={async () => await downloadMutation.mutateAsync()}><Download /></Button>
    )
}

export default DownloadPluginSrcButton;
