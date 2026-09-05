import axios from '@/axios'

// 接口前缀
const API_PREFIX = '/oss/file'

/**
 * 上传文件
 */
export function uploadFile(formData) {
  return axios.post(`${API_PREFIX}/upload`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}


