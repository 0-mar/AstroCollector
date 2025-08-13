import {Outlet, createRootRoute} from '@tanstack/react-router'
import {TanStackRouterDevtools} from '@tanstack/react-router-devtools'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
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
            <div className="m-8">
                <Outlet/>
            </div>
            <TanStackRouterDevtools/>
            <ReactQueryDevtools initialIsOpen={false} />
        </QueryClientProvider>
    )
    },
})
