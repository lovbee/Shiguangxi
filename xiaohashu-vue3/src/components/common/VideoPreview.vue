<template>
  <div class="video-preview-container">
    <!-- 视频预览遮罩层 -->
    <div 
      v-if="visible" 
      class="fixed inset-0 bg-black/80 backdrop-blur-sm z-[200] flex items-center justify-center p-4"
      @click="close"
    >
      <!-- 视频播放器容器 -->
      <div 
        class="relative max-w-[90vw] max-h-[90vh] rounded-lg overflow-hidden bg-black"
        @click.stop
      >
        <!-- 视频播放器 -->
        <video 
          ref="videoRef"
          :src="videoUrl" 
          class="max-w-full max-h-[90vh] object-contain"
          controls
          autoplay
        ></video>
        
        <!-- 关闭按钮 -->
        <button 
          class="absolute right-4 top-4 w-10 h-10 rounded-full bg-black/50 backdrop-blur-sm flex items-center justify-center hover:bg-black/70 transition-colors"
          @click="close"
        >
          <svg class="w-6 h-6 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M18 6L6 18M6 6l12 12" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  videoUrl: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:visible'])

const videoRef = ref(null)

// 关闭预览
const close = () => {
  emit('update:visible', false)
  
  // 暂停视频播放
  if (videoRef.value) {
    videoRef.value.pause()
  }
}

// 处理 ESC 按键关闭预览
const handleEscKey = (e) => {
  if (e.key === 'Escape' && props.visible) {
    close()
  }
}

// 监听可见性变化
watch(() => props.visible, (newValue) => {
  if (newValue) {
    // 当显示时，添加键盘事件监听
    document.addEventListener('keydown', handleEscKey)
    // 禁止背景滚动
    document.body.style.overflow = 'hidden'
  } else {
    // 当隐藏时，移除键盘事件监听
    document.removeEventListener('keydown', handleEscKey)
    // 恢复背景滚动
    document.body.style.overflow = ''
  }
})

// 组件挂载时添加键盘事件监听
onMounted(() => {
  if (props.visible) {
    document.addEventListener('keydown', handleEscKey)
    document.body.style.overflow = 'hidden'
  }
})

// 组件卸载时移除键盘事件监听
onUnmounted(() => {
  document.removeEventListener('keydown', handleEscKey)
  document.body.style.overflow = ''
})
</script>

<style scoped>
/* 视频控制器样式优化 */
video::-webkit-media-controls-panel {
  background-color: rgba(0, 0, 0, 0.5);
}

/* 确保视频容器响应式 */
.video-preview-container {
  width: 100%;
  height: 100%;
}
</style> 