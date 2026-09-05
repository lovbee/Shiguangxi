<template>
  <router-view></router-view>
  
  <!-- 登录模态框 -->
  <Teleport to="body">
    <LoginModal v-model:visible="showLoginModal" />
  </Teleport>
</template>

<script setup>
import { ref, provide, onMounted } from 'vue'
import LoginModal from '@/components/auth/LoginModal.vue'
import { useChannelStore } from '@/stores/channel'

const showLoginModal = ref(false)
provide('showLoginModal', showLoginModal)

const channelStore = useChannelStore()

onMounted(() => {
  // 加载频道数据
  channelStore.loadChannels()
})
</script>

<style scoped>
</style>
