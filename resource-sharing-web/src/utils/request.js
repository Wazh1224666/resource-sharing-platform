// src/utils/request.js
import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
    baseURL: 'http://localhost:8080/api', // 对应你后端的 context-path
    timeout: 5000,
    withCredentials: true // 允许发送凭据（CORS）
})

// 请求拦截器：自动把 Token 塞进 Header
// 请求拦截器
request.interceptors.request.use(config => {
    const token = localStorage.getItem('token');
    if (token) {
        // 注意：后端拦截器里写的是 getHeader("Authorization")
        config.headers['Authorization'] = token;
    }
    return config;
}, error => {
    return Promise.reject(error);
});

// 响应拦截器：处理 401 / 403 状态码
request.interceptors.response.use(response => {
    const bizCode = response?.data?.code
    if (bizCode === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('userInfo');
        ElMessage.warning(response?.data?.msg || '登录已过期，请重新登录');
        window.location.href = '/';
        return Promise.reject(new Error('Unauthorized'))
    }
    return response;
}, error => {
    if (error.response && error.response.status === 401) {
        // 如果后端返回 401，说明 Token 过期或无效，强制跳转回登录页
        localStorage.removeItem('token');
        localStorage.removeItem('userInfo');
        ElMessage.warning(error.response?.data?.msg || '登录已过期，请重新登录');
        window.location.href = '/';
    } else if (error.response && error.response.status === 403) {
        ElMessage.error(error.response?.data?.msg || '无权限执行该操作');
    }
    return Promise.reject(error);
})

export default request