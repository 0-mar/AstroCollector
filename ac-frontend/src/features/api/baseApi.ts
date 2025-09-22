import axios, {type AxiosRequestConfig} from 'axios';
import createAuthRefreshInterceptor from "axios-auth-refresh";
import {refreshAuth} from "@/features/api/refresh.ts";

export const axiosInstance = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
    withCredentials: true
});

createAuthRefreshInterceptor(axiosInstance, refreshAuth, {
    statusCodes: [401], // default: [ 401 ]
    pauseInstanceWhileRefreshing: true,
});


async function get<T>(path: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await axiosInstance.get<T>(path, config);
    return response.data;
}

async function post<T>(path: string, payload?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await axiosInstance.post<T>(path, payload, config);
    return response.data;
}



const BaseApi = {
    get,
    post
};

export default BaseApi;
