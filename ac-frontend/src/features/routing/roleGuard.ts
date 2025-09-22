import type {UserRoleEnum} from "@/features/auth/types.ts";
import {redirect, type BeforeLoadFn} from "@tanstack/react-router";


export const roleGuard = (permittedRoles: UserRoleEnum[]): BeforeLoadFn<any, any, any, any, any> => ({context, location}) => {
    if (!context.auth.isAuthenticated || !permittedRoles.includes(context.auth.user?.role?.name)) {
        throw redirect({
            to: '/login',
            search: {
                redirect: location.href,
            },
        })
    }
}
