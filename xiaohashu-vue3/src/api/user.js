import axios from '@/axios'

// 接口前缀
const API_PREFIX = '/user/user'

/**
 * 获取用户个人资料
 */
export function getUserProfile(userId) {
  return axios.post(`${API_PREFIX}/profile`, { userId: userId === 'undefined' ? null : userId })
}

/**
 * 更新用户资料
 */
export function updateUserProfile(data) {
  // 创建 FormData 对象用于文件上传
  const formData = new FormData()
  
  // 如果有头像文件，添加到表单
  if (data.avatar && data.avatar instanceof File) {
    formData.append('avatar', data.avatar)
  }
  
  // 添加其他字段
  if (data.nickname) formData.append('nickname', data.nickname)
  if (data.xiaohashuId) formData.append('xiaohashuId', data.xiaohashuId)
  if (data.sex !== undefined && data.sex !== null) formData.append('sex', data.sex)
  if (data.birthday) formData.append('birthday', data.birthday)
  if (data.introduction) formData.append('introduction', data.introduction)
  
  return axios.post(`${API_PREFIX}/update`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}


