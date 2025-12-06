import React, {createContext} from "react"
import BaseApi from "@/features/common/api/baseApi.ts";
import {useQuery, useQueryClient} from "@tanstack/react-query";
import type {User} from "@/features/common/auth/types.ts";


export type AuthCtx = {
    user: User | null;
    isAuthenticated: boolean;
    isPending: boolean;
    refetchUser: any;
    clearUser: any;
};

export const AuthContext = createContext<AuthCtx | null>(null)

export const AuthProvider = ({ children }: {children: React.ReactNode}) => {
    const queryClient = useQueryClient();
    const {
        data: user,
        isPending,
        refetch,
    } = useQuery({
        queryKey: ["current_user"],
        queryFn: async () => {
            try {
                return await BaseApi.get<User>("/security/me");
            } catch (e: any) {
                // if backend returns 401 when not logged in
                if (e?.response?.status === 401) return null;
                throw e;
            }

        },
        retry: false,
        staleTime: Infinity
    })

    const clearUser = () => {
        queryClient.setQueryData(["current_user"], null);
    };

    return (
        <AuthContext.Provider value={{
            user: user ?? null,
            isAuthenticated: !!user,
            isPending: isPending,
            refetchUser: refetch,
            clearUser: clearUser
        }}>
            {children}
        </AuthContext.Provider>
    );
};
