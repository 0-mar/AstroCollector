import {Outlet, createRootRoute} from '@tanstack/react-router'
import {TanStackRouterDevtools} from '@tanstack/react-router-devtools'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import {
    QueryClient,
    QueryClientProvider,
} from '@tanstack/react-query'

import Header from '../components/Header'
import Footer from "@/components/Footer.tsx";
import { Toaster } from "@/../components/ui/sonner"

export const Route = createRootRoute({
    component: () => {
    const queryClient = new QueryClient();
    return (
        <QueryClientProvider client={queryClient}>
            <Header/>
            <Outlet/>
            <TanStackRouterDevtools/>
            <ReactQueryDevtools initialIsOpen={false} />
            <Toaster />
            <Footer/>
        </QueryClientProvider>
    )
    },
})
