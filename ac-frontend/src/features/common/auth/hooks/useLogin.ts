import {useAuth} from "@/features/common/auth/hooks/useAuth.ts";
import {useNavigate, useSearch} from "@tanstack/react-router";
import {useMutation} from "@tanstack/react-query";
import BaseApi from "@/features/common/api/baseApi.ts";
import {toast} from "sonner";
import type {CsrfToken} from "@/features/common/auth/types.ts";

const useLogin = () => {
    const auth = useAuth()
    const navigate = useNavigate()
    const redirect = useSearch({from: "/login/"}) as { redirect?: string };

    return useMutation({
        mutationFn: ({email, password}: { email: string, password: string }) => {
            const params = new URLSearchParams();
            params.append("username", email);
            params.append("password", password);
            return BaseApi.post<CsrfToken>(`/security/login`, params, {headers: {"Content-Type": "application/x-www-form-urlencoded"}})
        },
        onError: (_error) => {
            toast.error("Login failed")
        },
        onSuccess: async (data) => {
            // at this point, backend set the ac_session cookie
            // refresh current user
            localStorage.setItem("ac_csrf_token", data.csrf_token)
            await auth?.refetchUser();
            const redirectPath = redirect?.redirect;
            await navigate({to: redirectPath ?? "/", replace: true});
        },
    })
}

export default useLogin
