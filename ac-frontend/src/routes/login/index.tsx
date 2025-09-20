import { createFileRoute } from "@tanstack/react-router"
import LoginForm from "@/components/auth/LoginForm.tsx";

export const Route = createFileRoute('/login/')({
    component: Login,
})

function Login(){
    return (
        <div className="flex flex-col justify-center items-center p-2">
            <h1>Log in</h1>
            <LoginForm />
        </div>
    )
}
