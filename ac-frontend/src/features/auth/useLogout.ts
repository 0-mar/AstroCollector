import {useMutation} from "@tanstack/react-query";
import BaseApi from "@/features/api/baseApi.ts";
import {toast} from "sonner";
import {removeHeaderToken} from "@/features/api/refresh.ts";
import {useAuth} from "@/features/auth/useAuth.ts";
import {useNavigate} from "@tanstack/react-router";

type LogoutMessage = {
    message: string
}

export const useLogout = () => {
    const auth = useAuth()
    const navigate = useNavigate()

    const logoutMutation = useMutation({
        mutationFn: () => {
            return BaseApi.post<LogoutMessage>(`/security/logout`)
        },
        onError: (_error) => {
            toast.error("Logout failed")
        },
        onSuccess: async () => {
            auth?.setAccessToken(null)
            removeHeaderToken()
            // TODO fixme: bug - login returns back to
            await navigate({ to: "/login", search: {redirect: "/"} });
        },
    });

    return logoutMutation
}
