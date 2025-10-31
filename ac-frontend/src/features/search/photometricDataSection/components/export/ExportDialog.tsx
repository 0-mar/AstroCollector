import { Button } from "../../../../../../components/ui/button.tsx"
import {
    Dialog,
    DialogClose,
    DialogContent,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "../../../../../../components/ui/dialog.tsx"
import {useMutation} from "@tanstack/react-query";
import BaseApi from "@/features/common/api/baseApi.ts";
import InfoAlert from "@/features/common/alerts/InfoAlert.tsx";
import { toast } from "sonner"
import type {StellarObjectIdentifierDto} from "@/features/search/menuSection/types.ts";
import {FileDown} from "lucide-react";
import {RadioGroup, RadioGroupItem} from "@/../components/ui/radio-group.tsx";
import {Label} from "@radix-ui/react-label";
import {ExportOptions} from "@/features/search/photometricDataSection/types.ts";
import React from "react";

type ExportDialogProps = {
    readyData: Array<[StellarObjectIdentifierDto, string]>,
    pluginNames: Record<string, string>
}

const ExportDialog = ({readyData, pluginNames}: ExportDialogProps) => {
    const [exportType, setExportType] = React.useState<ExportOptions>(ExportOptions.SINGLE_FILE)
    const exportMutation = useMutation({
        mutationFn: () => BaseApi.post<Blob>(`/export`, {filters: {"task_id__in": readyData.map(([_ident, taskId]) => taskId)}}, { params: {"export_option": exportType}, responseType: "blob"}),
        onError: (_error) => {
            toast.error("Failed to export data")
        },
        onSuccess: (data) => {
            const link = document.createElement("a");
            link.download = `export.zip`;
            link.href = URL.createObjectURL(data);
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
                <Button variant="outline"><FileDown />Export plot data</Button>
            </DialogTrigger>
            <DialogContent >
                <DialogHeader>
                    <DialogTitle className="text-xl">Export data</DialogTitle>
                </DialogHeader>

                <h3 className="text-lg">Export options</h3>
                <RadioGroup
                    className="mt-2"
                    value={exportType}
                    onValueChange={(value: ExportOptions) => setExportType(value)}
                >
                    <div className="flex items-center space-x-2">
                        <RadioGroupItem value={ExportOptions.SINGLE_FILE} id={ExportOptions.SINGLE_FILE} />
                        <Label htmlFor={ExportOptions.SINGLE_FILE}>Single file</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                        <RadioGroupItem value={ExportOptions.BY_SOURCES} id={ExportOptions.BY_SOURCES} />
                        <Label htmlFor={ExportOptions.BY_SOURCES}>By sources</Label>
                    </div>
                </RadioGroup>

                <InfoAlert title={"Data sources"}>
                    {readyData.map(([ident, _taskId]) => {
                        return <p key={ident.ra_deg + " " + ident.dec_deg + " " + ident.plugin_id}>{ident.ra_deg} {ident.dec_deg} ({pluginNames[ident.plugin_id]})</p>
                    })}
                </InfoAlert>
                <DialogFooter className="sm:justify-start">
                    <DialogClose asChild>
                        <Button onClick={() => exportMutation.mutateAsync()} type="button">
                            Export
                        </Button>
                    </DialogClose>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}

export default ExportDialog;
