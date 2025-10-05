import {useAuth} from "@/features/common/auth/hooks/useAuth.ts";
import React from "react";
import type {UserRoleEnum} from "@/features/common/auth/types.ts";

type ProtectedContentProps = {
    permittedRoles: UserRoleEnum[],
    children: React.ReactNode,
}

const ProtectedContent = ({permittedRoles, children}: ProtectedContentProps) => {
    const auth = useAuth();

    if (auth?.isAuthenticated && permittedRoles.includes(auth.user?.role?.name)) {
        return (
            <>
                {children}
            </>
        )
    }

    return null;
}

export default ProtectedContent;
