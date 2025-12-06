import {useAuth} from "@/features/common/auth/hooks/useAuth.ts";
import {useNavigate, useSearch} from "@tanstack/react-router";
import {useMutation} from "@tanstack/react-query";
import BaseApi from "@/features/common/api/baseApi.ts";
import {toast} from "sonner";

const useLogin = () => {
    const auth = useAuth()
    const navigate = useNavigate()
    const redirect = useSearch({from: "/login/"}) as { redirect?: string };

    const loginMutation = useMutation({
        mutationFn: ({email, password}: {email: string, password: string}) => {
            const params = new URLSearchParams();
            params.append("username", email);
            params.append("password", password);
            return BaseApi.post(`/security/login`, params, { headers: { "Content-Type": "application/x-www-form-urlencoded" } })
        },
        onError: (_error) => {
            toast.error("Login failed")
        },
        onSuccess: async () => {
            // at this point, backend set the ac_session cookie
            // refresh current user
            await auth?.refetchUser();
            const redirectPath = redirect?.redirect;
            await navigate({ to: redirectPath ?? "/", replace: true });
        },
    });

    return loginMutation
}

export default useLogin
