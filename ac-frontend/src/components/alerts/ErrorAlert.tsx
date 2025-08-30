import { Alert, AlertDescription, AlertTitle } from "../../../components/ui/alert.tsx"
import {CircleX} from "lucide-react";

const ErrorAlert = ({title, description}: {title: string, description: string}) => {
    return (
        <Alert className={"text-red-600 text-left"}>
            <CircleX />
            <AlertTitle>{title}</AlertTitle>
            <AlertDescription>
                {description}
            </AlertDescription>
        </Alert>
    )
}

export default ErrorAlert;
