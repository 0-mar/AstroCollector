import axios, {type AxiosRequestConfig} from 'axios';

export const axiosInstance = axios.create({
    baseURL: 'http://127.0.0.1:8000/api',
    //withCredentials: true
});

async function get<T>(path: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await axiosInstance.get<T>(path, config);
    return response.data;
}

async function post<T>(path: string, payload: unknown, config?: AxiosRequestConfig): Promise<T> {
    const response = await axiosInstance.post<T>(path, payload, config);
    return response.data;
}



const BaseApi = {
    get,
    post
};

export default BaseApi;
