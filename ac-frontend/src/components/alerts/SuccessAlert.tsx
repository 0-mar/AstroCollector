import {CircleCheck} from "lucide-react";
import {Alert, AlertDescription, AlertTitle} from "../../../components/ui/alert.tsx";
import type {AlertProps} from "@/components/alerts/alertProps.ts";


const SuccessAlert = ({title, description}: AlertProps) => {
    return (
        <Alert className={"text-green-700 text-left"}>
            <CircleCheck/>
            <AlertTitle>{title}</AlertTitle>
            <AlertDescription>
                {description}
            </AlertDescription>
        </Alert>
    )
}

export default SuccessAlert;
