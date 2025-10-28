import {useMutation, useQueryClient} from "@tanstack/react-query";
import {toast} from "sonner";
import BaseApi from "@/features/common/api/baseApi.ts";
import {Button} from "../../../../components/ui/button.tsx";
import {Trash, X} from "lucide-react";
import {
    Dialog,
    DialogClose,
    DialogContent, DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger
} from "../../../../components/ui/dialog.tsx";
import {useState} from "react";
import type {PluginDto} from "@/features/catalogsOverview/types.ts";

type DeletePluginButtonProps = {
    pluginDto: PluginDto
}

const DeletePluginDialog = ({pluginDto}: DeletePluginButtonProps) => {
    const queryClient = useQueryClient()
    const [open, setOpen] = useState(false);

    const deleteMutation = useMutation({
        onError: (_error) => {
            toast.error("Failed to delete plugin.")
        },
        mutationFn: () => {
            return BaseApi.delete<void>(`/plugins/${pluginDto.id}`)
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['plugins'] })
        },
        retry: (failureCount) => {
            return failureCount < 3;
        },
        retryDelay: (failureCount) => {
            return Math.min(1000 * 2 ** failureCount, 30000);
        },
    })

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button><Trash /></Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle>Delete <span className={"font-bold"}>{pluginDto.name}</span> catalog plugin</DialogTitle>
                </DialogHeader>
                <DialogDescription>
                    This action cannot be undone. Are you sure you want to permanently delete {pluginDto.name} catalog plugin?
                </DialogDescription>
                <DialogFooter className="sm:justify-start">
                    <Button onClick={async () => {await deleteMutation.mutateAsync(); setOpen(false)}} type="button">
                        Delete permanently
                    </Button>
                    <DialogClose asChild>
                        <Button variant={"secondary"}>
                            <X /> Close
                        </Button>
                    </DialogClose>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}

export default DeletePluginDialog;
