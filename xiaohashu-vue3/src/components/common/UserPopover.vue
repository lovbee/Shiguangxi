<template>
  <div class="relative inline-block">
    <!-- 触发元素插槽 -->
    <div 
      ref="triggerRef"
      @mouseenter="showPopover"
      @mouseleave="hidePopover"
    >
      <slot></slot>
    </div>

    <!-- 弹出卡片 -->
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="translate-y-1 opacity-0"
      enter-to-class="translate-y-0 opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="translate-y-0 opacity-100"
      leave-to-class="translate-y-1 opacity-0"
    >
      <div 
        v-if="visible"
        class="absolute z-50 bg-white rounded-lg shadow-xl border border-gray-100 
        p-6 w-[360px] flex flex-col gap-[16px]"
        :style="popoverStyle"
        @mouseenter="showPopover"
        @mouseleave="hidePopover"
      >

      <!-- @mouseleave="hidePopover" -->
        <div class="flex gap-[12px] items-center">
          <!-- 左侧头像 -->
          <div class="flex-shrink-0">
            <img 
              :src="user.avatar" 
              class="w-[40px] h-[40px] rounded-full border border-gray-200"
            />
          </div>

          <!-- 右侧内容区域 -->
          <div class="flex-1 min-w-0">
            <!-- 名字和关注按钮 -->
            <div class="flex items-center justify-between">
              <span class="font-bold text-[16px] text-[#333] truncate">{{ user.name }}</span>
              <button class="bg-[#ff2442] text-white h-[32px] w-[80px] px-[24px] 
              text-sm rounded-full hover:opacity-90 cursor-pointer">
                关注
              </button>
            </div>
          </div>
        </div>

        <!-- 简介 - 和头像对齐 -->
        <div class="text-[#333] text-sm">{{ user.description }}</div>

        <!-- 用户数据 - 和头像对齐 -->
        <div class="flex items-center justify-between text-center text-[14px]">
          <div class="flex items-center">
            <div class="font-medium text-[#333]">{{ user.notes }}</div>
            <div class="interaction-info">关注</div>
          </div>
          <div class="flex items-center">
            <div class="font-medium text-[#333]">{{ user.followers }}</div>
            <div class="interaction-info">粉丝</div>
          </div>
          <div class="flex items-center">
            <div class="font-medium text-[#333]">{{ user.likes }}</div>
            <div class="interaction-info">获赞与收藏</div>
          </div>
        </div>

        <!-- 笔记预览 - 和头像对齐 -->
        <div class="grid grid-cols-3 gap-[8px]">
          <div 
            v-for="note in user.recentNotes" 
            :key="note.id"
            class="aspect-square rounded-sm overflow-hidden"
          >
            <img 
              :src="note.cover" 
              class="w-full h-full object-cover hover:opacity-90 transition-opacity cursor-pointer"
              alt="note cover"
            />
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  user: {
    type: Object,
    required: true
  },
  placement: {
    type: String,
    default: 'bottom-start'
  }
})

const visible = ref(false)
const triggerRef = ref(null)
const triggerBounds = ref({
  height: 0,
  width: 0,
  top: 0,
  left: 0
})

// 更新元素位置信息
const updateBounds = () => {
  if (triggerRef.value) {
    const rect = triggerRef.value.getBoundingClientRect()
    triggerBounds.value = {
      height: rect.height,
      width: rect.width,
      top: rect.top,
      left: rect.left
    }
  }
}

// 计算弹出框位置
const popoverStyle = computed(() => {
  if (props.placement === 'bottom-start') {
    return {
      top: `${triggerBounds.value.height + 8}px`,
      left: '0'
    }
  }
  // 可以添加其他位置的计算...
})

let hideTimer = null

const showPopover = () => {
  if (hideTimer) {
    clearTimeout(hideTimer)
    hideTimer = null
  }
  visible.value = true
}

const hidePopover = () => {
  hideTimer = setTimeout(() => {
    visible.value = false
  }, 200)
}

onMounted(() => {
  updateBounds()
  window.addEventListener('resize', updateBounds)
  window.addEventListener('scroll', updateBounds)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', updateBounds)
  window.removeEventListener('scroll', updateBounds)
})
</script> 

<style scoped>
.interaction-info {
    color: rgba(51, 51, 51, 0.6);
    font-size: 14px;
    font-weight: 400;
    line-height: 120%;
    margin-left: 4px;
}
</style>
