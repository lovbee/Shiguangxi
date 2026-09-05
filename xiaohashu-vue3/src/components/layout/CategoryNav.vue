<template>
  <div class="category-nav flex items-center">
    <div class="flex items-center overflow-x-auto py-2 px-4 whitespace-nowrap">
      <!-- 全部频道 -->
      <div 
        class="channel"
        :class="{ 
          'active-channel': activeChannelId === 0,
          '': activeChannelId !== 0
        }"
        @click="handleChannelClick(0)"
      >
        全部
      </div>
      
      <!-- 动态获取的频道列表 -->
      <div 
        v-for="channel in channels" 
        :key="channel.id"
        class="channel"
        :class="{ 
          'active-channel': activeChannelId === channel.id,
          '': activeChannelId !== channel.id
        }"
        @click="handleChannelClick(channel.id)"
      >
        {{ channel.name }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useChannelStore } from '@/stores/channel'

const props = defineProps({
  activeChannelId: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['channel-change'])

const channelStore = useChannelStore()
const channels = ref([])

// 处理频道点击
const handleChannelClick = (channelId) => {
  // 触发自定义事件，将频道ID传递给父组件
  emit('channel-change', channelId)
}

// 组件挂载时获取频道列表
onMounted(async () => {
  // 如果 store 中已有频道数据，直接使用
  if (channelStore.channels.length > 0) {
    channels.value = channelStore.channels
  } else {
    // 否则获取频道数据
    await channelStore.loadChannels()
    channels.value = channelStore.channels
  }
})
</script>

<style scoped>
.category-nav {
  /* border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  background-color: #fff; */
  height: 72px;
}

/* 隐藏滚动条但保留功能 */
.overflow-x-auto {
  scrollbar-width: none; /* Firefox */
  -ms-overflow-style: none; /* IE and Edge */
}

.overflow-x-auto::-webkit-scrollbar {
  display: none; /* Chrome, Safari, Opera */
}

.channel {
    height: 40px;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 0 16px;
    cursor: pointer;
    -webkit-user-select: none;
    user-select: none;
    color: var(--color-secondary-label)
}

.channel:hover {
    background: var(--color-active-background);
    border-radius: 999px;
    color: var(--color-primary-label);
}

.active-channel {
    background: var(--color-active-background);
    border-radius: 999px;
    color: var(--color-primary-label);
    font-weight: 600;
}
</style> 