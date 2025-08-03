import axios from 'axios';

export const axiosInstance = axios.create({
    baseURL: 'http://127.0.0.1:8000/api',
    //withCredentials: true
});

async function getAll<T>(path: string, config?): Promise<T> {
    const response = await axiosInstance.get<T>(path, config);
    return response.data;
}

async function get<T>(path: string, config?) {
    const response = await axiosInstance.get<T>(path, config);
    return response.data;
}

async function postSingle<T>(path: string, payload: unknown): Promise<T> {
    const response = await axiosInstance.post<T>(path, payload);
    return response.data;
}

async function putSingle<T>(path: string, payload: unknown): Promise<T> {
    const response = await axiosInstance.put<T>(path, payload);
    return response.data;
}

async function deleteSingle<T>(path: string) {
    const resp = await axiosInstance.delete<T>(path);
    return resp.data;
}



const BaseApi = {
    getAll,
    get,
    postSingle,
    putSingle,
    deleteSingle,
};

export default BaseApi;
