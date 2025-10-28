import React, {createContext, useEffect, useMemo, useState} from "react"
import BaseApi from "@/features/common/api/baseApi.ts";
import {useQuery} from "@tanstack/react-query";
import type {User} from "@/features/common/auth/types.ts";
import {fetchNewToken, setHeaderToken} from "@/features/common/api/refresh.ts";


export type AuthCtx = {
    user: User | null;
    setUser: React.Dispatch<React.SetStateAction<User | null>>;
    accessToken: string | null;
    setAccessToken: React.Dispatch<React.SetStateAction<string | null>>
    isAuthenticated: boolean;
    isLoading: boolean;
};

export const AuthContext = createContext<AuthCtx | null>(null)

export const AuthProvider = ({ children }: {children: React.ReactNode}) => {
    const [user, setUser] = useState<User | null>(null)
    const [accessToken, setAccessToken] = useState<string | null>(null)
    const [isInitializing, setIsInitializing] = useState(true)

    // restore session on mount using refresh token cookie (when user opens new tab)
    useEffect(() => {
        const initializeAuth = async () => {
            try {
                console.log("Restoring session...");
                const token = await fetchNewToken();
                console.log(token);
                if (token) {
                    setAccessToken(token);
                    setHeaderToken(token);
                }
            } catch (error) {
                console.log("No valid session to restore");
            } finally {
                setIsInitializing(false);
            }
        };

        initializeAuth();
    }, []);

    const userQuery = useQuery({
        queryKey: ["user"],
        queryFn: () => BaseApi.get<User>("/security/me"),
        enabled: accessToken !== null && !isInitializing,
        retry: false,
    })

    useEffect(() => {
        if (userQuery.isSuccess) {
            setUser(userQuery.data)
        } else if (userQuery.isError) {
            setAccessToken(null)
            setUser(null)
        }
    }, [userQuery.isSuccess, userQuery.isError]);

    const values = useMemo<AuthCtx>(() => ({
        user,
        setUser,
        accessToken,
        setAccessToken,
        isAuthenticated: accessToken !== null && user !== null,
        isLoading: isInitializing || userQuery.isLoading,
    }), [user, accessToken, isInitializing, userQuery.isLoading])

    return (
        <AuthContext.Provider value={values}>
            {children}
        </AuthContext.Provider>
    );
};
