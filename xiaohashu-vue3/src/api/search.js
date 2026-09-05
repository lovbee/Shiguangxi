import axios from "@/axios";

// 接口前缀
const API_PREFIX = '/search/search'

// 搜索笔记
export function searchNote(keyword, type, sort, publishTimeRange, pageNo) {
    return axios.post(`${API_PREFIX}/note`, {keyword, type, sort, publishTimeRange, pageNo})
}

// 搜索用户
export function searchUser(keyword, pageNo) {
    return axios.post(`${API_PREFIX}/user`, {keyword, pageNo})
}


