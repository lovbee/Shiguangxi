import axios from "@/axios";

// 接口前缀
const API_PREFIX = '/comment/comment'

// 获取笔记一级评论分页数据
export function getCommentList(noteId, pageNo) {
    return axios.post(`${API_PREFIX}/list`, {noteId, pageNo})
}

// 发布评论
export function publishComment(comment) {
    return axios.post(`${API_PREFIX}/publish`, comment)
}

// 获取笔记二级评论分页数据
export function getChildCommentList(parentCommentId, pageNo) {
    return axios.post(`${API_PREFIX}/child/list`, {parentCommentId, pageNo})
}

// 点赞评论
export function likeComment(commentId) {
    return axios.post(`${API_PREFIX}/like`, {commentId})
}

// 取消点赞评论
export function unlikeComment(commentId) {
    return axios.post(`${API_PREFIX}/unlike`, {commentId})
}

