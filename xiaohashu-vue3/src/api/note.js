import axios from "@/axios";

// 接口前缀
const API_PREFIX = '/note'

// 发布笔记
export function publishNote(note) {
    return axios.post(`${API_PREFIX}/note/publish`, note)
}

// 获取发现页笔记数据
export function getDiscoverNotePageList(channelId, pageNo) {
    return axios.post(`${API_PREFIX}/discover/note/list`, {channelId, pageNo})
}

// 获取笔记详情
export function getNoteDetail(id) {
    return axios.post(`${API_PREFIX}/note/detail`, {id})
}

// 点赞笔记
export function likeNote(noteId) {
    return axios.post(`${API_PREFIX}/note/like`, {id: noteId})
}

// 取消点赞笔记
export function unlikeNote(noteId) {
    return axios.post(`${API_PREFIX}/note/unlike`, {id: noteId})
}

// 收藏笔记
export function collectNote(noteId) {
    return axios.post(`${API_PREFIX}/note/collect`, {id: noteId})
}

// 取消收藏笔记
export function uncollectNote(noteId) {
    return axios.post(`${API_PREFIX}/note/uncollect`, {id: noteId})
}

// 是否点赞、收藏
export function isLikedAndCollectedData(noteId) {
    return axios.post(`${API_PREFIX}/note/isLikedAndCollectedData`, {noteId})
}

// 获取个人主页笔记数据
export function getProfileNotePageList(type, userId, pageNo) {
    return axios.post(`${API_PREFIX}/profile/note/list`, {type, userId, pageNo})
}

