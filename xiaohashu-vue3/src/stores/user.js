import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useUserStore = defineStore('user', () => {
  const token = ref('')
  // 主页用户信息
  const profile = ref({})

  const setProfile = (newProfile) => {
    profile.value = newProfile
  }

  const setToken = (newToken) => {
    token.value = newToken
  }

  // 退出登录
  const logout = () => {
    token.value = ''
    // 删除用户信息
    profile.value = {}
  }


  return {
    token,
    profile,
    setProfile,
    setToken,
    logout,
  }
}, 
{
  // 开启持久化
  persist: true,
})