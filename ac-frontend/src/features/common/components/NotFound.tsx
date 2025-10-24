import {EyeOff} from "lucide-react";
import {Button} from "../../../../components/ui/button.tsx";
import {Link} from "@tanstack/react-router";

const NotFound = () => {
    return (
        <div className="flex flex-col items-center space-y-4 pt-6">
            <EyeOff width="80px" height="80px"/>
            <h1 className={"text-3xl font-extrabold"}>Not found</h1>
            <p>The page you were looking for does not exist.</p>
            <Link to="/"><Button>Go home</Button></Link>
        </div>
    )
}

export default NotFound;
