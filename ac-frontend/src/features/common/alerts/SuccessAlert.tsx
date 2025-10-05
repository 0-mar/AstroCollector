import {CircleCheck} from "lucide-react";
import {Alert, AlertDescription, AlertTitle} from "../../../../components/ui/alert.tsx";
import type {AlertProps} from "@/features/common/alerts/alertProps.ts";


const SuccessAlert = ({title, description}: AlertProps) => {
    return (
        <Alert className={"text-green-700 text-left bg-transparent border-green-900 border-2"}>
            <CircleCheck/>
            <AlertTitle>{title}</AlertTitle>
            <AlertDescription className={"text-green-700"}>
                {description}
            </AlertDescription>
        </Alert>
    )
}

export default SuccessAlert;
