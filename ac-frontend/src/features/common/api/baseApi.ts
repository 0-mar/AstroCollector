import axios, {type AxiosRequestConfig} from 'axios';

/**
 * An instance of Axios HTTP client configured for making HTTP requests to the AstroCollector API.
 */
export const axiosInstance = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
    withCredentials: true,
});

// use interceptor to send CSRF token with each request in the header
axiosInstance.interceptors.request.use((config) => {
    const token = localStorage.getItem("ac_csrf_token");

    if (token) {
        config.headers = config.headers ?? {};
        (config.headers as any)["X-CSRF-Token"] = token;
    }

    return config;
});

async function get<T>(path: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await axiosInstance.get<T>(path, config);
    return response.data;
}

async function post<T>(path: string, payload?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await axiosInstance.post<T>(path, payload, config);
    return response.data;
}

async function put<T>(path: string, payload?: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await axiosInstance.put<T>(path, payload, config);
    return response.data;
}

async function deleteHttp<T>(path: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await axiosInstance.delete<T>(path, config);
    return response.data;
}

async function getBlob(path: string, config?: AxiosRequestConfig) {
    const res = await axiosInstance.get<Blob>(path, { ...config, responseType: "blob" });
    return { blob: res.data, headers: res.headers };
}


const BaseApi = {
    get,
    post,
    put,
    delete: deleteHttp,
    getBlob
};

export default BaseApi;
