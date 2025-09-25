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
            <header className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-bold">Log in</h1>
            </header>
            <LoginForm />
        </div>
    )
}
