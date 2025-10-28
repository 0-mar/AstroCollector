import {useMutation} from "@tanstack/react-query";
import BaseApi from "@/features/common/api/baseApi.ts";
import {toast} from "sonner";
import {removeHeaderToken} from "@/features/common/api/refresh.ts";
import {useAuth} from "@/features/common/auth/hooks/useAuth.ts";
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
            // Even if API call fails, clear local state
            auth?.setAccessToken(null);
            auth?.setUser(null);
            removeHeaderToken();
            toast.error("Logout failed")
        },
        onSuccess: async () => {
            auth?.setAccessToken(null)
            auth?.setUser(null)
            removeHeaderToken()
            // TODO fixme: bug - login returns back to
            toast.success("Logged out successfully");
            await navigate({ to: "/login", search: {redirect: "/"} });
        }
    });

    return logoutMutation
}
