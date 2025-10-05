import {useAuth} from "@/features/common/auth/hooks/useAuth.ts";
import {useNavigate, useSearch} from "@tanstack/react-router";
import {useMutation} from "@tanstack/react-query";
import BaseApi from "@/features/common/api/baseApi.ts";
import type {Tokens} from "@/features/common/auth/types.ts";
import {toast} from "sonner";
import {setHeaderToken} from "@/features/common/api/refresh.ts";

const useLogin = () => {
    const auth = useAuth()
    const navigate = useNavigate()
    const redirect = useSearch({from: "/login/"}) as { redirect?: string };

    const loginMutation = useMutation({
        mutationFn: ({email, password}: {email: string, password: string}) => {
            const params = new URLSearchParams();
            params.append("username", email);
            params.append("password", password);
            return BaseApi.post<Tokens>(`/security/login`, params, { headers: { "Content-Type": "application/x-www-form-urlencoded" } })
        },
        onError: (_error) => {
            toast.error("Login failed")
        },
        onSuccess: async (data) => {
            auth?.setAccessToken(data.access_token)
            setHeaderToken(data.access_token)
            const redirectPath = redirect?.redirect;
            await navigate({ to: redirectPath ?? "/", replace: true });
        },
    });

    return loginMutation
}

export default useLogin
