import BaseApi, {axiosInstance} from "@/features/api/baseApi.ts";
import type {Tokens} from "@/features/auth/useAuth.ts";

export const setHeaderToken = (token: string) => {
    axiosInstance.defaults.headers.common.Authorization = `Bearer ${token}`;
};

export const removeHeaderToken = () => {
    //client.defaults.headers.common.Authorization = null;
    delete axiosInstance.defaults.headers.common.Authorization;
};


export const fetchNewToken = async () => {
    try {
        const token: string = await BaseApi.post<Tokens>("/security/refresh")
            .then(res => res.access_token);
        return token;
    } catch (error) {
        return null;
    }
};

export const refreshAuth = async (failedRequest: any) => {
    const newToken = await fetchNewToken();

    if (newToken) {
        failedRequest.response.config.headers.Authorization = "Bearer " + newToken;
        setHeaderToken(newToken);
        // you can set your token in storage too
        // setToken({ token: newToken });
        return Promise.resolve(newToken);
    } else {
        // you can redirect to login page here
        // router.push("/login");
        return Promise.reject();
    }
};
