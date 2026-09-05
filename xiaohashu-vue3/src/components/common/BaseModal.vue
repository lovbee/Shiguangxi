<template>
  <Teleport to="body">
    <!-- 遮罩层 -->
    <div 
      v-if="visible" 
      class="fixed inset-0 bg-black/25 backdrop-blur-sm z-[100]"
      @click="onClickMask"
    ></div>
    
    <!-- 模态框 -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="transform scale-95 opacity-0"
      enter-to-class="transform scale-100 opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="transform scale-100 opacity-100"
      leave-to-class="transform scale-95 opacity-0"
    >
      <div 
        v-if="visible" 
        class="fixed inset-0 z-[101] flex items-center justify-center p-4"
      >
        <div 
          class="bg-white rounded-lg shadow-xl max-h-[90vh] flex flex-col"
          :style="{ width: width }"
          @click.stop
        >
          <!-- 标题栏 -->
          <div class="p-6 flex items-center justify-between border-b border-gray-100">
            <h2 class="text-[18px] font-bold text-gray-800">{{ title }}</h2>
            <button 
              class="w-8 h-8 flex items-center justify-center hover:bg-gray-100/80 rounded-full transition-colors"
              @click="onClose"
            >
              <svg class="w-5 h-5 text-gray-500" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M18 6L6 18M6 6l12 12" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <!-- 内容区域 -->
          <div class="flex-1 overflow-y-auto">
            <slot></slot>
          </div>

          <!-- 底部按钮区域 -->
          <div 
            v-if="showFooter"
            class="px-6 py-4 border-t border-gray-100 flex justify-end gap-3"
          >
            <button 
              class="cursor-pointer px-6 h-10 font-bold rounded-full border border-gray-200 text-gray-600 hover:bg-gray-50"
              @click="onClose"
            >
              取消
            </button>
            <button 
              class="cursor-pointer px-6 h-10 font-bold rounded-full bg-[#ff2442] text-white hover:opacity-90"
              @click="$emit('confirm')"
            >
              确定
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    required: true
  },
  width: {
    type: String,
    default: '480px'
  },
  showFooter: {
    type: Boolean,
    default: true
  },
  closeOnClickMask: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['update:visible', 'confirm'])

const onClose = () => {
  emit('update:visible', false)
}

const onClickMask = () => {
  if (props.closeOnClickMask) {
    onClose()
  }
}

// 处理 ESC 按键
const handleEscKey = (e) => {
  if (e.key === 'Escape' && props.visible) {
    onClose()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleEscKey)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscKey)
})
</script>

<style scoped>
/* 自定义滚动条样式 */
.overflow-y-auto {
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 0, 0, 0.1) transparent;
}

.overflow-y-auto::-webkit-scrollbar {
  width: 6px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: transparent;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}
</style> 