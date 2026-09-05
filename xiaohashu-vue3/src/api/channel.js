import axios from "@/axios";

// 接口前缀
const API_PREFIX = '/note/channel'

// 获取所有频道
export function getAllChannel() {
    return axios.post(`${API_PREFIX}/list`)
}

