import {Alert, AlertDescription, AlertTitle} from "../../../../components/ui/alert.tsx";
import {Info} from "lucide-react";
import React from "react";

type InfoAlertProps = {
    title: string,
    children: React.ReactNode,
}

const InfoAlert = ({title, children}: InfoAlertProps) => {
    return (
        <Alert className={"text-gray-900 text-left"}>
            <Info />
            <AlertTitle>{title}</AlertTitle>
            <AlertDescription>
                {children}
            </AlertDescription>
        </Alert>
    )
}

export default InfoAlert;
