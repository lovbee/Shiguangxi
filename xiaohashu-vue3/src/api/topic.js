import axios from "@/axios";

// 接口前缀
const API_PREFIX = '/note/topic'

// 获取所有频道
export function getTopicList(keyword) {
    return axios.post(`${API_PREFIX}/list`, {keyword})
}

