<template>
  <div class="note-card">
    <div 
      class="relative rounded-lg overflow-hidden"
      @click="$emit('click', note)"
    >
      <img v-if="note.type === 0"
        :src="note.cover" 
        class="w-full object-cover border border-gray-200 rounded-2xl hover:brightness-80 cursor-pointer"
      />
      
      <video v-if="note.type === 1"
          ref="videoRef"
          :src="note.videoUri" 
          class="w-full object-cover border border-gray-200 rounded-2xl hover:brightness-80 cursor-pointer"
          preload="metadata"
          muted
        ></video>

      <div v-if="note.type === 1" class="absolute right-2 top-2 play-icon">
        <svg class="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
          <path d="M8 5v14l11-7z"/>
        </svg>
      </div>
    </div>

    <div class="p-[12px]">
      <h3 class="note-title">{{ note.title }}</h3>
      <div class="flex items-center">
        <router-link :to="`/user/profile/${note.creatorId}`">
          <img
          v-if="note.avatar"
          :src="note.avatar" 
          class="w-[20px] h-[20px] mr-[6px] rounded-full border border-gray-200"
        />
          <div 
            v-else 
            class="w-[20px] h-[20px] mr-[6px] rounded-full border border-gray-200
             flex items-center justify-center bg-gray-100 text-gray-400"
          >
            <svg class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2" stroke-width="2" stroke-linecap="round"/>
              <circle cx="12" cy="7" r="4" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </div>
        </router-link>
        <span class="text-[12px] text-gray-600 hover:text-gray-800 flex-1 truncate">
          <router-link :to="`/user/profile/${note.creatorId}`">
            {{ note.nickname }}
          </router-link>
        </span>
        <button 
          class="flex items-center transition-colors group"
          @click.stop="toggleLike"
        >
          <svg 
            class="w-[16px] h-[16px] transition-all duration-300" 
            :class="{'scale-animation': isLiked}"
            viewBox="0 0 24 24" 
            :style="{
              fill: isLiked ? '#fe2c55' : 'none',
              stroke: isLiked ? '#fe2c55' : 'currentColor'
            }"
            stroke-width="2"
          >
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
          </svg>
          <span 
            class="ml-1 text-[12px] text-gray-600 transition-all duration-300"
            :class="{'scale-animation': isLiked}"
          >
            {{ likeCount || 0 }}
          </span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, inject } from 'vue'
import { likeNote, unlikeNote } from '@/api/note'
import { message } from '@/utils/message'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

const props = defineProps({
  note: {
    type: Object,
    required: true
  }
})

defineEmits(['click'])

// 点赞状态
const isLiked = ref(false)
const likeCount = ref(props.note.likeTotal)


// 登录状态控制
const isLoggedIn = computed(() => !!userStore.token)
const showLoginModal = inject('showLoginModal')

// 切换点赞状态
const toggleLike = () => {
  if (!isLoggedIn.value) {
    showLoginModal.value = true
    return
  }


  // 更新点赞数
  if (!isLiked.value) {
    likeNote(props.note.id).then(res => {
      console.log('点赞了, ' + props.note.id)
      if (res.success) {
        // 如果是数字，就加1
        if (!isNaN(likeCount.value)) {
          likeCount.value = parseInt(likeCount.value) + 1
        }
      } else {
        message.show(res.message)
      }
    })
    
  } else {
    unlikeNote(props.note.id).then(res => {
      console.log('取消点赞了, ' + props.note.id)
      if (res.success) {
        // 如果是数字，就减1
        if (!isNaN(likeCount.value)) {
          likeCount.value = Math.max(0, parseInt(likeCount.value) - 1)
        }
      } else {
        message.show(res.message)
      }
    })
  }
  isLiked.value = !isLiked.value
}
</script>

<style scoped>
.note-title {
    margin-bottom: 8px;
    word-break: break-all;
    display: -webkit-box;
    -webkit-box-orient: vertical;
    -webkit-line-clamp: 2;
    overflow: hidden;
    font-weight: 500;
    font-size: 14px;
    line-height: 140%;
    color: #333;
}

/* 点赞动画 */
@keyframes scale {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    transform: scale(1);
  }
}

.scale-animation {
  animation: scale 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* 悬浮效果 */
button:hover svg {
  transform: scale(1.1);
}

.play-icon {
  display: flex
;
    align-items: center;
    justify-content: center;
    position: absolute;
    right: 14px;
    top: 14px;
    width: 20px;
    height: 20px;
    color: #fff;
    background: rgba(64,64,64,0.25);
    backdrop-filter: saturate(150%) blur(10px);
    border-radius: 20px;
}
</style>