import {createFileRoute, redirect} from "@tanstack/react-router"
import LoginForm from "@/components/auth/LoginForm.tsx";

export const Route = createFileRoute('/login/')({
    component: Login,
    validateSearch: (search) => ({
        redirect: (search.redirect as string) || '/',
    }),
    beforeLoad: ({ context, search }) => {
        // Redirect if already authenticated
        if (context.auth.isAuthenticated) {
            throw redirect({ to: search.redirect })
        }
    },
})

function Login(){
    return (
        <div className="flex flex-col justify-center items-center p-2">
            <h1>Log in</h1>
            <LoginForm />
        </div>
    )
}
