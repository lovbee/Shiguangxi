<template>
  <Transition
    name="fade"
    appear
  >
    <div 
      v-if="visible" 
      class="loading-overlay pb-5"
    >
      <div class="spinner-container">
        <div class="spinner"></div>
        <div v-if="text" class="loading-text">{{ text }}</div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  // 加载时显示的文本
  text: {
    type: String,
    default: ''
  },
  // 最小显示时间（毫秒）
  minDuration: {
    type: Number,
    default: 500
  }
})

// 控制加载器的可见性
const visible = ref(false)
// 记录显示开始时间
let showStartTime = 0
// 记录隐藏请求时间
let hideRequestTime = 0
// 隐藏定时器
let hideTimer = null

// 显示加载器
const show = () => {
  // 清除可能存在的隐藏定时器
  if (hideTimer) {
    clearTimeout(hideTimer)
    hideTimer = null
  }
  
  // 记录显示开始时间
  showStartTime = Date.now()
  visible.value = true
}

// 隐藏加载器
const hide = () => {
  // 记录隐藏请求时间
  hideRequestTime = Date.now()
  
  // 计算已显示时间
  const elapsedTime = hideRequestTime - showStartTime
  
  // 如果已显示时间小于最小持续时间，则延迟隐藏
  if (elapsedTime < props.minDuration) {
    const remainingTime = props.minDuration - elapsedTime
    hideTimer = setTimeout(() => {
      visible.value = false
      hideTimer = null
    }, remainingTime)
  } else {
    // 已经显示足够长时间，直接隐藏
    visible.value = false
  }
}

// 暴露方法给父组件
defineExpose({
  show,
  hide
})
</script>

<style scoped>
.loading-overlay {
  width: 100%;
  height: 100%;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(2px);
}

.spinner-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.spinner {
  width: 25px;
  height: 25px;
  border: 3px solid rgba(255, 36, 66, 0.2);
  border-radius: 50%;
  border-top-color: #ff2442;
  animation: spin 1s ease-in-out infinite;
}


@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.loading-text {
    font-size: 12px;
    line-height: 18px;
    text-align: center;
    color: var(--color-tertiary-label);
    margin-top: 10px;
}
</style> 