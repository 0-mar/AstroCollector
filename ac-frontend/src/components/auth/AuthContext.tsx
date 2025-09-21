import React, {createContext, useEffect, useMemo, useState} from "react"
import BaseApi from "@/features/api/baseApi.ts";
import {useQuery} from "@tanstack/react-query";
import type {User} from "@/features/auth/types.ts";


export type AuthCtx = {
    user: User | null;
    setUser: React.Dispatch<React.SetStateAction<User | null>>;
    accessToken: string | null;
    setAccessToken: React.Dispatch<React.SetStateAction<string | null>>
    isAuthenticated: boolean;
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

    const values = useMemo<AuthCtx>(() => ({
        user,
        setUser,
        accessToken,
        setAccessToken,
        isAuthenticated: accessToken !== null && user !== null,
    }), [user, accessToken])

    return (
        <AuthContext.Provider value={values}>
            {children}
        </AuthContext.Provider>
    );
};
