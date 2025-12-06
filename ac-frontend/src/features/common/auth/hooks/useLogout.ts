import {useMutation} from "@tanstack/react-query";
import BaseApi from "@/features/common/api/baseApi.ts";
import {toast} from "sonner";
import {useAuth} from "@/features/common/auth/hooks/useAuth.ts";
import {useNavigate} from "@tanstack/react-router";

type LogoutMessage = {
    message: string
}

export const useLogout = () => {
    const auth = useAuth()
    const navigate = useNavigate()

    return useMutation({
        mutationFn: () => {
            return BaseApi.post<LogoutMessage>(`/security/logout`)
        },
        onError: (_error) => {
            // Even if API call fails, clear local state
            auth?.clearUser()
            toast.error("Logout failed")
        },
        onSuccess: async () => {
            auth?.clearUser()
            toast.success("Logged out successfully");
            await navigate({to: "/login", search: {redirect: "/"}});
        }
    })
}
