import { RouterProvider, createRouter } from "@tanstack/react-router";
import { routeTree } from "./routeTree.gen";
import {QueryClient, QueryClientProvider} from "@tanstack/react-query";
import {AuthProvider} from "@/features/common/auth/components/AuthContext.tsx";
import {useAuth} from "@/features/common/auth/hooks/useAuth.ts";

export const router = createRouter({
    routeTree,
    context: {
        auth: {
            isAuthenticated: false,
            user: null,
            accessToken: null
        }
    },
    //defaultPreload: 'intent',
    //scrollRestoration: true,
    //defaultStructuralSharing: true,
    //defaultPreloadStaleTime: 0,
})

declare module "@tanstack/react-router" {
    interface Register {
        router: typeof router;
    }
}

const queryClient = new QueryClient()

const AppRouter = () => {
    const auth = useAuth()
    return (
        <RouterProvider
            router={router}
            context={{
                auth: {
                    isAuthenticated: auth?.isAuthenticated ?? false,
                    accessToken: auth?.accessToken ?? null,
                    user: auth?.user ?? null,
                },
            }}
        />
    )
}

function App() {
    return (
        <QueryClientProvider client={queryClient}>
            <AuthProvider>
                <AppRouter />
            </AuthProvider>
        </QueryClientProvider>
    )
}

export default App;
