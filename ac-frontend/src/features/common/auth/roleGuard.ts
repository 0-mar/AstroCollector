import type {UserRoleEnum} from "@/features/common/auth/types.ts";
import {redirect, type BeforeLoadFn} from "@tanstack/react-router";

/**
 * A guard function that restricts access to a Route based on user roles.
 *
 * @param {UserRoleEnum[]} permittedRoles - An array of roles that are allowed access.
 * @throws Will throw a redirect to the login page if the user is not authenticated or their role is not permitted.
 */
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
