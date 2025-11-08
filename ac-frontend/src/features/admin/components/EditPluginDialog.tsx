import {Button} from "../../../../components/ui/button.tsx";
import {Save, SquarePen, X} from "lucide-react";
import {
    Dialog,
    DialogClose,
    DialogContent,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger
} from "../../../../components/ui/dialog.tsx";
import {useState} from "react";
import EditPluginForm from "@/features/admin/components/EditPluginForm.tsx";
import type {PluginDto} from "@/features/catalogsOverview/types.ts";
import useUpdateCatalogPlugin from "@/features/catalogsOverview/hooks/useUpdateCatalogPlugin.ts";


type EditPluginButtonProps = {
    pluginDto: PluginDto
}

const EditPluginDialog = ({pluginDto}: EditPluginButtonProps) => {
    const [open, setOpen] = useState(false);
    const formId = `edit-plugin-${pluginDto.id}-form`;
    const update = useUpdateCatalogPlugin(pluginDto.id)
    const { mutation } = update;

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button variant="outline"><SquarePen /></Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle>Edit {pluginDto.name} plugin</DialogTitle>
                </DialogHeader>

                <EditPluginForm
                    pluginDto={pluginDto}
                    formId={formId}
                    setOpen={setOpen}
                    mutation={mutation}
                    phase={update.phase}
                    overallProgress={update.overallProgress}
                />

                <DialogFooter className="sm:justify-start">
                    <Button type="submit" form={formId} disabled={mutation.isPending}>
                        <Save /> Save changes
                    </Button>
                    <DialogClose asChild>
                        <Button type="button" variant="secondary" disabled={mutation.isPending}>
                            <X /> Close and discard changes
                        </Button>
                    </DialogClose>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}

export default EditPluginDialog;
