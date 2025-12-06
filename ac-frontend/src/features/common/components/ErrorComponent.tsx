import {TriangleAlert} from "lucide-react";
import {Link} from "@tanstack/react-router";
import {Button} from "@/../components/ui/button.tsx";

const ErrorComponent = () => {
    return (
        <div className="flex flex-col items-center space-y-4 pt-6">
            <TriangleAlert width="80px" height="80px"/>
            <h1 className={"text-3xl font-extrabold"}>An error has occured</h1>
            <Link to="/"><Button>Go home</Button></Link>
        </div>
    )
}

export default ErrorComponent;
