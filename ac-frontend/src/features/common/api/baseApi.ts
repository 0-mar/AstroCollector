import axios, {type AxiosRequestConfig} from 'axios';

export const axiosInstance = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
    withCredentials: true
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
