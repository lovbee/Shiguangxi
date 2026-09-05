import axios from "@/axios";

// 接口前缀
const API_PREFIX = '/relation/relation'

// 关注用户
export function followUser(followUserId) {
    return axios.post(`${API_PREFIX}/follow`, {followUserId})
}

// 获取关注列表
export function getFollowingList(userId, pageNo) {
    return axios.post(`${API_PREFIX}/following/list`, {userId, pageNo})
}

// 获取粉丝列表
export function getFansList(userId, pageNo) {
    return axios.post(`${API_PREFIX}/fans/list`, {userId, pageNo})
}


