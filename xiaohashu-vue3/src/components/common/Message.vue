<template>
  <Transition name="fade">
    <div 
      v-if="visible"
      class="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-[10000] bg-[#333] text-white px-6 py-3
       rounded-full whitespace-nowrap font-bold"
    >
      {{ message }}
    </div>
  </Transition>
</template>

<script setup>
import { ref } from 'vue'

const visible = ref(false)
const message = ref('')

// 显示消息
const show = (msg, duration = 2000) => {
  message.value = msg
  visible.value = true
  
  setTimeout(() => {
    visible.value = false
  }, duration)
}

// 暴露方法给外部使用
defineExpose({
  show
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style> 