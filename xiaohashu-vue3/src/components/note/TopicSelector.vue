<template>
  <div class="relative">
    <!-- 话题输入框 -->
    <div class="flex items-center border-b border-gray-100 py-3">
      <span class="text-[#ff2442] text-[14px] font-medium mr-2">#</span>
      <input
        ref="inputRef"
        v-model="keyword"
        type="text"
        placeholder="搜索添加话题"
        class="flex-1 text-[14px] focus:outline-none"
        @input="onInput"
        @keydown.enter="onEnter"
        @keydown.backspace="onBackspace"
      />
    </div>

    <!-- 已选话题展示 -->
    <div class="flex flex-wrap gap-2 mt-3">
      <div
        v-for="topic in selectedTopics"
        :key="topic.id"
        class="px-3 py-1.5 bg-gray-50 rounded-full text-[14px] text-gray-800 flex items-center gap-1"
      >
        <span class="text-[#ff2442]">#</span>
        {{ topic.name }}
        <button 
          class="ml-1 p-0.5 hover:bg-gray-200 rounded-full"
          @click="removeTopic(topic)"
        >
          <svg class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M18 6L6 18M6 6l12 12" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- 搜索结果下拉框 -->
    <div 
      v-if="showDropdown && suggestions.length" 
      class="absolute left-0 right-0 top-[100%] bg-white rounded-lg shadow-lg mt-1 py-2 max-h-[300px] overflow-auto z-10"
    >
      <div
        v-for="topic in suggestions"
        :key="topic.id"
        class="px-4 py-2 hover:bg-gray-50 cursor-pointer flex items-center"
        @click="selectTopic(topic)"
      >
        <span class="text-[#ff2442] mr-1">#</span>
        <div>
          <div class="text-[14px] text-gray-800">{{ topic.name }}</div>
          <div class="text-[12px] text-gray-400">{{ topic.noteCount }}个笔记</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue'])

const keyword = ref('')
const suggestions = ref([])
const showDropdown = ref(false)
const inputRef = ref(null)

const selectedTopics = ref(props.modelValue)

// 监听外部传入的值变化
watch(() => props.modelValue, (newVal) => {
  selectedTopics.value = newVal
})

// 搜索话题 - 模拟接口
const searchTopics = async (kw) => {
  // TODO: 替换为真实接口
  return [
    { id: 1, name: kw + '推荐', noteCount: 1234 },
    { id: 2, name: kw + '热门', noteCount: 5678 },
    { id: 3, name: kw + '相关', noteCount: 9012 }
  ]
}

// 自定义防抖函数
const debounce = (fn, delay) => {
  let timer = null
  return (...args) => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn.apply(this, args)
    }, delay)
  }
}

// 使用自定义防抖函数替代 useDebounceFn
const debouncedSearch = debounce(async (kw) => {
  if (!kw) {
    suggestions.value = []
    showDropdown.value = false
    return
  }
  suggestions.value = await searchTopics(kw)
  showDropdown.value = true
}, 300)

// 输入处理
const onInput = () => {
  debouncedSearch(keyword.value)
}

// 选择话题
const selectTopic = (topic) => {
  if (selectedTopics.value.some(t => t.id === topic.id)) {
    return
  }
  selectedTopics.value = [...selectedTopics.value, topic]
  emit('update:modelValue', selectedTopics.value)
  keyword.value = ''
  showDropdown.value = false
  inputRef.value?.focus()
}

// 移除话题
const removeTopic = (topic) => {
  selectedTopics.value = selectedTopics.value.filter(t => t.id !== topic.id)
  emit('update:modelValue', selectedTopics.value)
}

// 回车处理
const onEnter = () => {
  if (suggestions.value.length) {
    selectTopic(suggestions.value[0])
  }
}

// 退格键处理
const onBackspace = (e) => {
  if (!keyword.value && selectedTopics.value.length) {
    e.preventDefault()
    selectedTopics.value = selectedTopics.value.slice(0, -1)
    emit('update:modelValue', selectedTopics.value)
  }
}
</script> 