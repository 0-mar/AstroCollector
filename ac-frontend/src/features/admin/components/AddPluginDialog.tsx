import {Button} from "../../../../components/ui/button.tsx";
import {CirclePlus, Save, X} from "lucide-react";
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
import AddPluginForm from "@/features/admin/components/AddPluginForm.tsx";
import useCreateCatalogPlugin from "@/features/catalogsOverview/hooks/useCreateCatalogPlugin.ts";



const AddPluginDialog = () => {
    const [open, setOpen] = useState(false);
    const formId = `add-plugin-form`;

    const create = useCreateCatalogPlugin();
    const { mutation } = create;

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button variant="outline"><CirclePlus />Add catalog plugin</Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle>Add catalog plugin</DialogTitle>
                </DialogHeader>

                <AddPluginForm
                    formId={formId}
                    setOpen={setOpen}
                    mutation={mutation}
                    phase={create.phase}
                    overallProgress={create.overallProgress}
                />

                <DialogFooter className="sm:justify-start">
                    <Button type="submit" form={formId} disabled={mutation.isPending}>
                        <Save /> Save plugin
                    </Button>
                    <DialogClose asChild>
                        <Button type="button" variant="secondary" disabled={mutation.isPending}>
                            <X /> Close and discard plugin
                        </Button>
                    </DialogClose>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}

export default AddPluginDialog;
