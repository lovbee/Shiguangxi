import axios from "axios";
import { message } from "@/utils/message";
import { useUserStore } from "@/stores/user";

// 创建 Axios 实例
const instance = axios.create({
    baseURL: '/api',
    timeout: 15000, // 请求超时时间
    // HTTP 接口与 WebSocket 都依赖 Gateway 写入的同源 HttpOnly Sa-Token Cookie。
    // Authorization 头仍保留给既有接口和已登录的本地状态作为兼容路径。
    withCredentials: true,
});



// 添加请求拦截器
instance.interceptors.request.use(function (config) {
    // 从 localStorage 获取 token
    const userStore = useUserStore();
    const token = userStore.token;
    
    // 如果存在 token，则添加到请求头
    if (token) {
        // 添加请求头, key 为 Authorization，value 值的前缀为 'Bearer '
        config.headers['Authorization'] = `Bearer ${token}`;
    }

    return config;
}, function (error) {
    // 对请求错误做些什么
    return Promise.reject(error);
});

// 添加响应拦截器
instance.interceptors.response.use(function (response) {
    // 2xx 范围内的状态码都会触发该函数。
    // 对响应数据做点什么
    return response.data;
}, function (error) {
    
    // 超出 2xx 范围的状态码都会触发该函数。
    // 对响应错误做点什么
    let status = error.response?.status

    if (status === 401) {
        console.log("====================== 401")
        message.show('请先登录');
        
        // 获取 store 实例并清除登录状态
        const userStore = useUserStore();
        userStore.logout();
    } else {
        // 显示错误信息
        const msg = error.response?.data?.message || '请求失败';
        message.show(msg);
    }
    
    return Promise.reject(error);
});

// 暴露出去
export default instance;
