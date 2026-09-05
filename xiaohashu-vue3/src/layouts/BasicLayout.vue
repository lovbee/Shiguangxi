<template>
  <div class="h-screen max-w-screen-3xl mx-auto">
    <div>
      <!-- 顶部导航栏 -->
      <AppHeader />

      <div class="flex h-[calc(100vh-72px)] px-5 2xl:px-24 pt-[76px]">
        <!-- 左侧侧边栏 -->
        <AppSidebar />

        <!-- 右侧内容区域 -->
        <main class="px-5 grow ml-[320px]">

          
          <router-view></router-view>
        </main>
      </div>
    </div>
  </div>
</template>

<script setup>
import AppHeader from '@/components/layout/AppHeader.vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'

</script>

<style scoped>
</style> 