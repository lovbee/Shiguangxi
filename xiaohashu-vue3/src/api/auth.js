import axios from "@/axios";

// 接口前缀
const API_PREFIX = '/auth'

// 获取登录验证码
export function getVerificationCode(phone) {
    return axios.post(`${API_PREFIX}/verification/code/send`, {phone})
}

// 登录接口
export function login(loginReqVO) {
    return axios.post(`${API_PREFIX}/login`, loginReqVO)
}

// 退出登录接口
export function logout() {
    return axios.post(`${API_PREFIX}/logout`)
}
