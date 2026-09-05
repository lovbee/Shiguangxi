<template>
  <div 
    :class="[
      !isReply && 'p-[8px]',
      !isReply && 'mb-[16px]',
      comment.isNewComment && 'new-comment-animation'
    ]"
    class="flex py-[8px]"
  >
    <!-- <UserPopover :user="comment.author">
      <img 
        :src="comment.avatar" 
        :class="[
          'rounded-full cursor-pointer',
          isReply ? 'w-[24px] h-[24px]' : 'w-[40px] h-[40px]'
        ]"
      />
    </UserPopover> -->
    <img 
        :src="comment.avatar" 
        :class="[
          'rounded-full cursor-pointer',
          isReply ? 'w-[24px] h-[24px]' : 'w-[40px] h-[40px]'
        ]"
      />

    <div class="flex-1 ml-[12px]">
      <!-- 评论者信息 -->
      <div class="flex items-center justify-between">
        <div>
          <!-- <UserPopover :user="comment.author">
            <span class="name cursor-pointer">{{ comment.nickname }}</span>
          </UserPopover> -->
          <span class="name cursor-pointer">{{ comment.nickname }}</span>
        </div>
      </div>
      
      <!-- 评论内容 -->
      <div class="content">
        <span v-if="comment.replyUserName">回复 <span class="reply-nickname">{{ comment.replyUserName }}</span> :</span>
        {{ comment.content }}
      </div>

      <!-- 评论图片 -->
      <div v-if="comment.imageUrl" class="mt-[8px]">
        <img 
          :src="comment.imageUrl" 
          class="w-[120px] rounded-lg object-cover cursor-zoom-in hover:brightness-80"
          @click="showPreview = true"
        />
      </div>

      <!-- 图片预览 -->
      <ImagePreview
        v-model:visible="showPreview"
        :images="[comment.imageUrl]"
      />

      <div class="info my-[8px]">{{ comment.createTime }}</div>

      <!-- 评论底部操作区 -->
      <div class="flex items-center gap-2 text-gray-500 text-[12px] interactions">
        
        <!-- 点赞 -->
        <div 
          class="flex items-center gap-1 cursor-pointer hover:text-gray-800 ml-[2px]"
          @click="toggleLike"
        >
          <svg 
            class="w-[16px] h-[16px] transition-all duration-200"
            :class="[isLiked ? 'animate-like' : 'animate-unlike']"
            viewBox="0 0 24 24" 
            :fill="isLiked ? '#ff2442' : 'none'" 
            :stroke="isLiked ? '#ff2442' : 'currentColor'"
          >
            <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" stroke-width="2"/>
          </svg>
          <span :class="{ 'text-[#ff2442]': isLiked }">{{ comment.likeTotal }}</span>
        </div>

        <!-- 回复 -->
        <div 
          class="flex items-center gap-1 cursor-pointer hover:text-gray-800"
          @click="onReplyClick"
        >
          <svg class="w-[16px] h-[16px]" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" stroke-width="2"/>
          </svg>
          <span>回复</span>
        </div>
      </div>

      <!-- 子评论区域 -->
      <template v-if="comment.childCommentTotal > 0">
        <!-- 已加载的子评论列表 -->
        <div v-if="comment.childComments && comment.childComments.length > 0" class="mt-2">
          <div>
            <CommentItem 
              v-for="(childComment, index) in comment.childComments" 
              :key="index"
              :comment="childComment"
              :is-reply="true"
              @reply="$emit('reply', $event)"
              @like="$emit('like', $event)"
            />
          </div>
        </div>
        
        <!-- 展开回复按钮 -->
        <div 
          v-if="comment.childCommentTotal > 1 && 
                (!comment.childComments || comment.childComments.length < comment.childCommentTotal) && 
                comment.hasMoreChildComments !== false"
          class="show-more mt-2"
          @click="handleExpandReplies(comment)"
        >
          {{ comment.childComments?.length > 1 ? '展开更多回复' : `展开 ${comment.childCommentTotal - 1} 条回复` }}
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import ImagePreview from '@/components/common/ImagePreview.vue'
import UserPopover from '@/components/common/UserPopover.vue'

const props = defineProps({
  comment: {
    type: Object,
    required: true,
    validator(comment) {
      return comment.author && {
        ...comment.author,
        description: '好看的皮囊千篇一律，有趣的灵魂万里挑一',
        notes: '1290',
        followers: '8.9w',
        likes: '12.9w',
        recentNotes: [
          {
            id: 1,
            cover: 'https://sns-webpic-qc.xhscdn.com/202502181653/a7981c8c78a90db57af9e4ba3054adb0/1040g00831cmai18ggk6g4a4d62jppumfdrcjnco!nc_n_webp_mw_1'
          },
          // ... 更多笔记
        ]
      }
    }
  },
  isReply: {
    type: Boolean,
    default: false
  }
})

const showPreview = ref(false)
const isLiked = ref(false)
const localLikes = ref(Number(props.comment.likes) || 0)

// 计算显示的点赞数
const displayLikes = computed(() => {
  return isLiked.value ? localLikes.value + 1 : localLikes.value
})

// 修改 emit 定义，添加 like 事件
const emit = defineEmits(['reply', 'expand-replies', 'like'])

// 修改点赞切换函数
const toggleLike = () => {
  isLiked.value = !isLiked.value
  // 触发点赞事件，传递整个 comment 对象和点赞状态
  emit('like', { comment: props.comment, liked: isLiked.value })
}

// 点击回复
const onReplyClick = () => {
  emit('reply', props.comment)
}

// 添加展开回复的点击处理
const handleExpandReplies = (comment) => {
  emit('expand-replies', comment)
}
</script>

<style scoped>
.name {
    color: rgba(51, 51, 51, 0.6);
    line-height: 18px;
    font-size: 14px;
}

.name:hover {
    color: rgba(51, 51, 51, 0.8);
}

.content {
    margin-top: 4px;
    line-height: 140%;
    color: #333;
    font-size: 14px;
}


.info {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    font-size: 12px;
    line-height: 16px;
    color: rgba(51, 51, 51, 0.6);
}

.interactions {
    font-size: 12px;
    line-height: 16px;
    color: rgba(51, 51, 51, 0.6);
}

.interactions {
  color: rgba(51, 51, 51, 0.6);
  font-size: 12px;
  line-height: 16px;
  white-space: nowrap;
}

.interactions svg {
  flex-shrink: 0;
}

.show-more {
    margin-left: 38px;
    height: 20px;
    line-height: 20px;
    color: #13386c;
    cursor: pointer;
    font-weight: 500;
    font-size: 14px;
}

@keyframes like {
  0% {
    transform: scale(1);
  }
  25% {
    transform: scale(0.8);
  }
  50% {
    transform: scale(1.2);
  }
  75% {
    transform: scale(0.95);
  }
  100% {
    transform: scale(1);
  }
}

@keyframes unlike {
  0% {
    transform: scale(1);
  }
  25% {
    transform: scale(0.9);
  }
  50% {
    transform: scale(1.1);
  }
  75% {
    transform: scale(0.95);
  }
  100% {
    transform: scale(1);
  }
}

.animate-like {
  animation: like 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  transform-origin: center;
}

.animate-unlike {
  animation: unlike 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  transform-origin: center;
}

/* 防止动画重复播放 */
.animate-like, .animate-unlike {
  animation-fill-mode: forwards;
}

/* 防止动画过程中文字抖动 */
.interactions span {
  min-width: 1.5em;
  display: inline-block;
  text-align: left;
}

/* 新评论动画效果 */
.new-comment-animation {
  animation: highlightNewComment 2s ease-out forwards;
}

@keyframes highlightNewComment {
  0% {
    background-color: rgba(255, 36, 66, 0.1);
  }
  100% {
    background-color: transparent;
  }
}

.reply-nickname {
  color: rgba(51, 51, 51, 0.6);
}
</style>
