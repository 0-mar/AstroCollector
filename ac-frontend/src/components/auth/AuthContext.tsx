import React, {createContext, useEffect, useState} from "react"
import BaseApi from "@/features/api/baseApi.ts";
import {useQuery} from "@tanstack/react-query";

enum UserRoleEnum {
    SUPER_ADMIN = "ROLE_SUPER_ADMIN",
    ADMIN = "ROLE_ADMIN",
    USER = "ROLE_USER",
}

type UserRole = {
    name: UserRoleEnum
    description: string | null
}

export type User = {
    username: string,
    email: string,
    disabled: boolean,
    created_at: string,
    role: UserRole
}

type AuthCtx = {
    user: User;
    setUser: React.Dispatch<React.SetStateAction<User>>;
    accessToken: string | null;
    setAccessToken: React.Dispatch<React.SetStateAction<string>>
};

export const AuthContext = createContext<AuthCtx | null>(null)

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState<User | null>(null)
    const [accessToken, setAccessToken] = useState<string | null>(null)

    const userQuery = useQuery({
        queryKey: ["user"],
        queryFn: () => BaseApi.get<User>("/security/me", /*{
            headers: {
                'Authorization': `Bearer ${accessToken}`,
            }
        }*/),
        enabled: accessToken !== null
    })

    useEffect(() => {
        if (userQuery.isSuccess) {
            setUser(userQuery.data)
            console.log(userQuery.data)
        }
    }, [userQuery.isSuccess]);

    const values = {
        user,
        setUser,
        accessToken,
        setAccessToken
    }

    return (
        <AuthContext.Provider value={values}>
            {children}
        </AuthContext.Provider>
    );
};
