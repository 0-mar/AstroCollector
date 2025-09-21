import { createFileRoute, redirect, Outlet } from '@tanstack/react-router'
import {UserRoleEnum} from "@/features/auth/types.ts";

export const Route = createFileRoute('/_superAdmin')({
    beforeLoad: ({ context, location }) => {
        if (context.auth?.user?.role.name !== UserRoleEnum.SUPER_ADMIN) {
            throw redirect({
                to: '/login',
                search: {
                    // Save current location for redirect after login
                    redirect: location.href,
                },
            })
        }
    },
    component: () => <Outlet />,
})
