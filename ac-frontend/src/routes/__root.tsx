import {Outlet, createRootRouteWithContext} from '@tanstack/react-router'
import {TanStackRouterDevtools} from '@tanstack/react-router-devtools'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

import Header from '../components/Header'
import Footer from "@/components/Footer.tsx";
import { Toaster } from "@/../components/ui/sonner"
import type {User} from "@/features/auth/types.ts";

export type RouterCtx = {
    auth: {
        isAuthenticated: boolean;
        accessToken: string | null;
        user: User | null;
    };
};

export const Route = createRootRouteWithContext<RouterCtx>()({
    component: () => {
    return (
        <div className="min-h-dvh flex flex-col">
            <div className={"shrink-0"}>
                <Header/>
            </div>
            <main className="flex-1">
                <Outlet />
            </main>
            <div className={"shrink-0"}>
                <Footer/>
            </div>

            <TanStackRouterDevtools/>
            <ReactQueryDevtools initialIsOpen={false} />
            <Toaster />

        </div>
    )
    },
})
