<template>
  <div class="user-card flex items-center justify-between p-[20px] hover:bg-gray-50 transition-colors">
    <!-- 左侧用户信息 -->
    <router-link :to="`/user/profile/${user.userId}`" class="flex-1">
      <div class="flex items-center">
        <!-- 头像 -->
        <div class="flex-shrink-0">
          <img 
            :src="user.avatar" 
            class="avatar"
          />
        </div>
        
        <!-- 用户信息 -->
        <div class="user-info">
          <h3 class="nickname">{{ user.nickname }}</h3>
          <div v-if="type === 'user'" class="mt-[6px]">
            <span>小红书号：{{ user.xiaohashuId }}</span>
          </div>
          <div v-if="type === 'user' || type === 'fans'" class="mt-[6px] flex items-center">
            <span>粉丝・{{ user.fansTotal || 0 }}
              <span class="divider"></span>
            </span>
            <span>笔记・{{ user.noteTotal || 0 }}</span>
          </div>

          <div v-if="type === 'following'" class="mt-[6px] flex items-center">
            <span>{{ user.introduction || '此用户还未填写简介' }}
            </span>
          </div>

        </div>
      </div>
    </router-link>
    
    <!-- 右侧关注按钮 - 根据关注状态显示不同样式 -->
    <button 
      :class="[
        'follow-button', 
        user.isLiked ? 'followed' : ''
      ]"
      @click="handleFollow"
    >
      {{ user.isLiked ? '已关注' : '关注' }}
    </button>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'
import { useUserStore } from '@/stores/user'

const props = defineProps({
  type: {
    type: String,
    required: true,
    default: 'user'
  },
  user: {
    type: Object,
    required: true,
    default: () => ({
      userId: '',
      nickname: '',
      avatar: '',
      xiaohashuId: '',
      fansTotal: 0,
      noteTotal: 0,
      isLiked: true,
      introduction: ''
    })
  }
})

const emit = defineEmits(['follow'])
const userStore = useUserStore()

// 处理关注按钮点击
const handleFollow = () => {
  console.log('点击关注了')
  // 检查用户是否已登录
  if (!userStore.token) {
    // 可以触发登录弹窗
    emit('login-required')
    return
  }
  
  // 触发关注事件
  emit('follow', props.user.userId)
}

</script>

<style scoped>
.user-card {
  border-radius: 16px;
}

.user-card:hover {
  background-color: var(--color-active-background);
}

/* 文本溢出省略 */
.line-clamp-1 {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.avatar {
    width: 72px;
    height: 72px;
    border-radius: 72px;
    border: 1px solid var(--color-border);
    object-fit: cover;
    background: var(--color-active-background);
}

.user-info {
    display: flex;
    flex-direction: column;
    color: var(--color-tertiary-label);
    font-size: 14px;
    font-weight: 400;
    line-height: 120%;
    margin: 0 20px;
    width: 100%;
}

.nickname {
    display: flex;
    align-items: center;
    /* justify-content: center; */
    color: var(--color-primary-label);
    font-size: 18px;
    font-weight: 600;
    line-height: 120%;
    margin-right: 6px;
    white-space: nowrap;
}

.divider {
    margin: 0 8px;
    display: inline-block;
    height: 12px;
    border: .5px solid var(--color-border);
}

.follow-button {
    cursor: pointer;
    -webkit-user-select: none;
    user-select: none;
    white-space: nowrap;
    outline: none;
    background: none;
    border: none;
    vertical-align: middle;
    text-align: center;
    display: inline-block;
    padding: 0;
    border-radius: 100px;
    font-weight: 500;
    background-color: #ff2e4d;
    color: #fff;
    font-size: 16px;
    font-weight: 600;
    line-height: 16px;
    padding: 0 24px;
    height: 40px;
    width: 96px;
}
</style> 