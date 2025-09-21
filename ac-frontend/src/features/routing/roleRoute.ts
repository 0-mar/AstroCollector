import type {UserRoleEnum} from "@/features/auth/types.ts";
import {createFileRoute, redirect, type FileRoutesByPath} from "@tanstack/react-router";

export const createFileRouteWithRoleProtection = (path: keyof FileRoutesByPath | undefined, permittedRoles: UserRoleEnum[], component: any) => {
    return createFileRoute(path)({
        beforeLoad: ({ context, location }) => {
            if (!permittedRoles.includes(context.auth.user?.role?.name)) {
                throw redirect({
                    to: '/',
                    search: {
                        redirect: location.href,
                    },
                })
            }
        },
        component: component
    })
}
