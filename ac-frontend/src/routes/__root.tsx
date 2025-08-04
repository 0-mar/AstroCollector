import {Outlet, createRootRoute} from '@tanstack/react-router'
import {TanStackRouterDevtools} from '@tanstack/react-router-devtools'
import {
    QueryClient,
    QueryClientProvider,
} from '@tanstack/react-query'

import Header from '../components/Header'

export const Route = createRootRoute({
    component: () => {
    const queryClient = new QueryClient();
    return (
        <QueryClientProvider client={queryClient}>
            <Header/>
            <Outlet/>
            <TanStackRouterDevtools/>
        </QueryClientProvider>
    )
    },
})
