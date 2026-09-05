import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getAllChannel } from '@/api/channel'

export const useChannelStore = defineStore('channel', () => {
  // 存储所有频道数据
  const channels = ref([])
  
  // 加载所有频道数据
  const loadChannels = async () => {
    try {
      const res = await getAllChannel()
      console
      if (res.success && res.data) {
        channels.value = res.data
      }
    } catch (error) {
      console.error('加载频道数据失败:', error)
    }
  }
  
  // 根据ID获取频道名称
  const getChannelNameById = (id) => {
    const channel = channels.value.find(item => item.id === id)
    return channel ? channel.name : ''
  }
  
  return {
    channels,
    loadChannels,
    getChannelNameById
  }
}) 