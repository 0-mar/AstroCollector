import {RouterProvider, createRouter} from "@tanstack/react-router";
import { routeTree } from "./routeTree.gen";
import {QueryClient, QueryClientProvider} from "@tanstack/react-query";
import {AuthProvider} from "@/features/common/auth/components/AuthContext.tsx";
import {useAuth} from "@/features/common/auth/hooks/useAuth.ts";
import NotFound from "@/features/common/components/NotFound.tsx";
import LoadingSkeleton from "@/features/common/loading/LoadingSkeleton.tsx";

export const router = createRouter({
    routeTree,
    context: {
        auth: {
            isAuthenticated: false,
            user: null,
            accessToken: null
        }
    },
    defaultNotFoundComponent: () => NotFound(),
    defaultPreload: 'intent',
    scrollRestoration: true,
})

declare module "@tanstack/react-router" {
    interface Register {
        router: typeof router;
    }
}

const queryClient = new QueryClient()

const AppRouter = () => {
    const auth = useAuth()
    // CRITICAL: Don't render router until auth is initialized
    if (auth?.isLoading) {
        console.log("Loading auth...")
        return (
            <div className="flex items-center justify-center min-h-screen">
                <LoadingSkeleton text={"Loading..."} />
            </div>
        );
    }

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
