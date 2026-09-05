<template>
  <div v-if="visible" class="fixed inset-0 flex items-center justify-center" style="z-index: 10000;">
    <!-- 遮罩层 -->
    <div class="absolute inset-0 bg-gray-800/25" @click="onClose"></div>
    
    <!-- 确认框 -->
    <div class="relative bg-white rounded-lg w-[320px] text-center">
      <h3 class="text-[16px] font-bold mb-[16px] mt-[24px] text-[#333]">阅读并同意</h3>
      
      <div class="text-[16px] text-[#13386c] mb-[24px]">
        <div>《用户协议》《隐私政策》</div>
        <div>《儿童/青少年个人信息保护规则》</div>
      </div>

      <div class="py-[6px] mx-2 flex-col items-center justify-center border-t border-gray-100">
        <button 
          class="h-10 block w-full rounded-lg font-bold text-gray-600 hover:text-gray-800 hover:bg-gray-100"
          @click="onConfirm"
        >
          同意并继续
        </button>
        <button 
          class="h-10 block w-full rounded-lg font-bold text-gray-600 hover:text-gray-800 hover:bg-gray-100"
          @click="onClose"
        >
          取消
        </button>

      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:visible', 'confirm'])

const onClose = () => {
  emit('update:visible', false)
}

const onConfirm = () => {
  emit('confirm')
  onClose()
}
</script> 