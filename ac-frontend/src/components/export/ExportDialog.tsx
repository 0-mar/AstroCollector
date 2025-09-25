import { Button } from "@/../components/ui/button"
import {
    Dialog,
    DialogClose,
    DialogContent,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/../components/ui/dialog"
import {useMutation} from "@tanstack/react-query";
import BaseApi from "@/features/api/baseApi.ts";
import InfoAlert from "@/components/alerts/InfoAlert.tsx";
import { toast } from "sonner"
import type {StellarObjectIdentifierDto} from "@/features/search/menu/types.ts";

type ExportDialogProps = {
    readyData: Array<[StellarObjectIdentifierDto, string]>,
    pluginNames: Record<string, string>
}

const ExportDialog = ({readyData, pluginNames}: ExportDialogProps) => {

    const exportMutation = useMutation({
        mutationFn: () => BaseApi.post<string>(`/export/csv`, {"task_id__in": readyData.map(([_ident, taskId]) => taskId)}),
        onError: (_error) => {
            toast.error("Failed to export data")
        },
        onSuccess: (data) => {
            const link = document.createElement("a");
            link.download = `export.csv`;
            const blob = new Blob([data], { type: "text/csv" });
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
    });


    return (
        <Dialog>
            <DialogTrigger asChild>
                <Button variant="outline">Export data</Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle>Export data</DialogTitle>
                </DialogHeader>
                <InfoAlert title={"Data sources"}>
                    {readyData.map(([ident, _taskId]) => {
                        return <p key={ident.ra_deg + " " + ident.dec_deg + " " + ident.plugin_id}>{ident.ra_deg} {ident.dec_deg} ({pluginNames[ident.plugin_id]})</p>
                    })}
                </InfoAlert>
                <DialogFooter className="sm:justify-start">
                    <DialogClose asChild>
                        <Button onClick={() => exportMutation.mutateAsync()} type="button" variant="secondary">
                            Export
                        </Button>
                    </DialogClose>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}

export default ExportDialog;
