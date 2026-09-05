<template>
  <!-- header 本身保持全宽，添加白色背景和阴影 -->
  <div class="flex items-center ">
    <header class="fixed top-0 z-30 w-full px-5 2xl:px-24 h-[72px] bg-white">
    <!-- 内容区域使用容器宽度限制 -->
    <div class="h-full mx-auto flex items-center relative">
      <!-- logo 容器，与左侧栏对齐 -->
      <div class="pl-10">
        <a href="/" class="block select-none text-2xl font-bold text-[#ff2442] no-underline">
          时光溪
        </a>
      </div>
      <!-- 搜索框容器 -->
      <div class="flex justify-center grow">
        <div class="relative">
          <input 
            v-model="searchKeyword"
            type="text" 
            placeholder="搜索小哈书" 
            class="w-[480px] h-10 px-4 py-2 rounded-full bg-[#f6f6f6] focus:outline-none text-sm caret-[#ff2442]"
            @keyup.enter="handleSearch"
          />
          <div class="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
            <!-- 删除按钮 -->
            <button 
              v-if="searchKeyword"
              class="w-5 h-5 flex items-center justify-center text-gray-500 hover:text-gray-600"
              @click="searchKeyword = ''"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M18 6L6 18M6 6l12 12" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
            <button class="cursor-pointer" @click="handleSearch">
              <!-- 搜索图标 -->
              <svg class="w-5 h-5 text-gray-500 hover:text-gray-600" viewBox="0 0 24 24" fill="none">
                <path d="M21 21L16.65 16.65M19 11C19 15.4183 15.4183 19 11 19C6.58172 19 3 15.4183 3 11C3 6.58172 6.58172 3 11 3C15.4183 3 19 6.58172 19 11Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
      <!-- 右侧按钮容器 -->
      <div class="flex items-center">
        <span class="cursor-not-allowed text-gray-600 px-5 py-2.5 rounded-full hover:bg-gray-100 hover:text-gray-800">创作中心</span>
      </div>
    </div>
  </header>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
const searchKeyword = ref(route.query.keyword || '')

// 处理搜索
const handleSearch = () => {
  if (!searchKeyword.value.trim()) return
  router.push({
    name: 'Search',
    query: { keyword: searchKeyword.value.trim() }
  })
}
</script> 
