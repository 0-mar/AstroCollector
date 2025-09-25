import {Button} from "../../../components/ui/button.tsx";
import {CirclePlus, Save, X} from "lucide-react";
import {
    Dialog,
    DialogClose,
    DialogContent,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger
} from "../../../components/ui/dialog.tsx";
import {useState} from "react";
import AddPluginForm from "@/components/admin/AddPluginForm.tsx";



const AddPluginDialog = () => {
    const [open, setOpen] = useState(false);
    const formId = `add-plugin-form`;

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button variant="outline"><CirclePlus />Add catalog plugin</Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle>Add catalog plugin</DialogTitle>
                </DialogHeader>

                <AddPluginForm formId={formId} setOpen={setOpen} />

                <DialogFooter className="sm:justify-start">
                    <Button type="submit" form={formId}>
                        <Save /> Save plugin
                    </Button>
                    <DialogClose asChild>
                        <Button type="button" variant="secondary">
                            <X /> Close and discard plugin
                        </Button>
                    </DialogClose>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}

export default AddPluginDialog;
