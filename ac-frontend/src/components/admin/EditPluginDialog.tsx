import {Button} from "../../../components/ui/button.tsx";
import {Save, SquarePen, X} from "lucide-react";
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
import EditPluginForm from "@/components/admin/EditPluginForm.tsx";
import type {PluginDto} from "@/features/plugin/types.ts";


type EditPluginButtonProps = {
    pluginDto: PluginDto
}

const EditPluginDialog = ({pluginDto}: EditPluginButtonProps) => {
    const [open, setOpen] = useState(false);
    const formId = `edit-plugin-${pluginDto.id}-form`;

    return (
        <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
                <Button variant="outline"><SquarePen /></Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle>Edit {pluginDto.name} plugin</DialogTitle>
                </DialogHeader>

                <EditPluginForm pluginDto={pluginDto} formId={formId} setOpen={setOpen}/>

                <DialogFooter className="sm:justify-start">
                    <Button type="submit" form={formId}>
                        <Save /> Save changes
                    </Button>
                    <DialogClose asChild>
                        <Button type="button" variant="secondary">
                            <X /> Close and discard changes
                        </Button>
                    </DialogClose>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    )
}

export default EditPluginDialog;
