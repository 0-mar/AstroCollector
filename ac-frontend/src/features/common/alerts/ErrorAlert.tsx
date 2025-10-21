import { Alert, AlertDescription, AlertTitle } from "../../../../components/ui/alert.tsx"
import {TriangleAlert} from "lucide-react";

const ErrorAlert = ({title, description}: {title: string, description: string}) => {
    return (
        <Alert className={"text-red-600 text-left border-2 border-red-700"}>
            <TriangleAlert />
            <AlertTitle>{title}</AlertTitle>
            <AlertDescription className={"text-red-600"}>
                {description}
            </AlertDescription>
        </Alert>
    )
}

export default ErrorAlert;
