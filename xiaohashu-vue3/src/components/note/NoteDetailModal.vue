<template>
  <Teleport to="body">
    <!-- 遮罩层 -->
    <div v-if="visible" class="fixed inset-0 bg-gray-800/25 z-[100]" @click="onClose"></div>
    
    <!-- 笔记详情 -->
    <Transition 
      name="zoom"
      appear
      @before-enter="onBeforeEnter"
      @enter="onEnter"
      @leave="onLeave"
    >
      <div v-if="visible" class="fixed inset-0 z-[101] pointer-events-none">
        <div 
          class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-white h-[90vh] 
          max-w-[90%] md:max-w-[85%] lg:max-w-[80%] xl:max-w-[70%] 2xl:max-w-[60%] w-auto rounded-lg flex overflow-hidden pointer-events-auto"
          ref="modalRef"
        >
          <!-- 左侧图片区域 -->
          <div class="h-full flex-1 flex items-center justify-center overflow-hidden">
            <div class="h-full w-full flex items-center justify-center">
              <ImageCarousel v-if="currNote.type === 0" :images="currNote.imgUris || []" class="h-full w-full" />
              <VideoPlayer v-else
                      :video-url="currNote.videoUri" 
                      :autoplay="true"
                    ></VideoPlayer>
            </div>
          </div>

          <!-- 右侧内容区域 -->
          <div class="w-[480px] min-w-[480px] flex flex-col bg-white">

            <!-- 作者信息 -->
            <div 
              class="p-[24px] flex items-center sticky top-0 bg-white"
              :class="{'border-b border-gray-100': isScrolled}"
              ref="authorInfoRef"
            >
              <router-link :to="`/user/profile/${currNote.creatorId}`">
                      <img 
                      :src="currNote.avatar" 
                      class="w-[40px]! h-[40px]! rounded-full"
                    />
              </router-link>

              <router-link :to="`/user/profile/${currNote.creatorId}`" class="ml-[12px] flex-1">
                      <div class="font-medium text-[16px] text-gray-600 hover:text-gray-800">{{ currNote.creatorName }}</div>
              </router-link>
              

              <button 
              v-if="!userStore.token || userStore.profile.userId !== currNote.creatorId"
              @click="handleFollow"
              class="bg-[#ff2442] text-white px-6 py-2 rounded-full font-bold hover:opacity-90 w-[96px] h-[40px] cursor-pointer">
                关注
              </button>
            </div>

            <!-- 评论区域容器 -->
            <div 
              class="overflow-y-auto flex-1" 
              @scroll="handleScroll"
              ref="scrollContainerRef"
            >
              <!-- 笔记正文 -->
              <div 
                class="text-[#333] px-[24px] pb-[24px] flex-1"
                ref="contentRef"
              >
                <h1 class="title">{{ currNote.title }}</h1>
                <div class="note-conten whitespace-pre-wrap">{{ currNote.content }}</div>
                <ul v-if="currNote.topics && currNote.topics.length > 0" class="text-[#13386c] flex flex-wrap gap-2">
                  <li v-for="(topic, index) in currNote.topics" :key="index" class="cursor-pointer">#{{topic.name}}</li>
                </ul>
                <div class="text-gray-500 text-[14px] mt-[12px]">
                  编辑于 {{ currNote.updateTime }}
                </div>
              </div>

              <!-- 分割线 -->
              <div class="h-[1px] border-b border-gray-100 mx-[24px]"></div>

              <!-- 评论区 -->
              <CommentList
                :comments="comments"
                :total="commentTotal"
                :has-more="hasMoreComments"
                :more-count="moreCommentsCount"
                @load-more="loadMoreComments"
                @reply="onReplyClick"
                @click-comment="focusComment"
                @expand-replies="handleExpandReplies"
                @like="handleCommentLike"
              />
            </div>
            

            <!-- 底部互动区 -->
            <div class="border-t border-gray-100 p-[16px]">
              <div class="flex flex-col text-gray-500 text-[15px]">
                <!-- 评论输入区域 -->
                <div class="flex items-center gap-2">
                  <!-- 登录提示/评论输入框 -->
                  <div 
                    v-if="!isLoggedIn"
                    class="content-input grow cursor-pointer"
                    @click="focusComment"
                  >
                    <svg class="w-4 h-4 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z" stroke-width="2"/>
                    </svg>
                    <span class="text-gray-500 text-sm ml-2">登录后评论</span>
                  </div>
                  
                  <!-- 已登录状态显示评论输入框 -->
                  <div 
                    v-else
                    class="flex flex-col"
                    :class="{ 'w-full': isInputFocused }"
                  >
                    <!-- 回复提示 - 仅在回复时显示 -->
                    <div 
                      v-if="replyTo"
                      class="flex flex-col px-3 py-2 text-[14px] w-full"
                    >
                      <div class="flex items-center reply">
                        回复
                        <span class="text-[#333] mx-1">{{ replyTo.nickname }}</span>
                      </div>
                      <div class="reply-content line-clamp-1">
                        {{ replyTo.content }} <span v-if="replyTo.imageUrl">[图片]</span>
                      </div>
                    </div>

                    <!-- 评论输入框 -->
                    <div 
                      class="gap-2 rounded-full flex items-center content-input"
                      :class="{
                        'w-full px-[16px]!': isInputFocused,
                        'w-[200px]': !isInputFocused
                      }"
                      @click="focusComment"
                    >
                      <!-- 头像只在未聚焦时显示 -->
                      <img 
                        v-if="!isInputFocused"
                        :src="userStore.profile.avatar" 
                        class="w-[24px] h-[24px] rounded-full shrink-0"
                      />
                      
                      <!-- 未聚焦时显示默认文本 -->
                      <div 
                        v-if="!isInputFocused && !commentContent" 
                        class="text-gray-500 text-sm ml-2 whitespace-nowrap overflow-hidden text-ellipsis"
                      >
                        说点什么...
                      </div>
                      
                      <!-- 输入框 -->
                      <input 
                        type="text" 
                        placeholder="说点什么..." 
                        v-model="commentContent"
                        class="flex-1 bg-transparent focus:outline-none min-w-0 text-[#333]"
                        :class="{
                          'ml-2 text-sm': !isInputFocused,
                          'text-[16px]': isInputFocused
                        }"
                        @blur="onInputBlur"
                        ref="commentInput"
                      />
                      
                    </div>
                    
                    <div class="mt-[8px]" v-if="commentImage">
                      <img :src="commentImage" 
                      class="w-[60px]! rounded-lg object-cover cursor-zoom-in hover:brightness-80 ml-2">
                    </div>
                  </div>

                  <!-- 互动数据 - 仅在输入框未聚焦时显示 -->
                  <div v-if="!isInputFocused" class="flex items-center gap-4 ml-auto text-[#333]">
                    <div class="flex items-center gap-1 cursor-pointer hover:text-gray-800">
                      <svg 
                        class="w-[20px] h-[20px] transition-all duration-200"
                        :class="[isNoteLiked ? 'animate-like' : 'animate-unlike']"
                        viewBox="0 0 24 24" 
                        :fill="isNoteLiked ? '#ff2442' : 'none'" 
                        :stroke="isNoteLiked ? '#ff2442' : 'currentColor'"
                        @click="handleNoteLike"
                      >
                        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" stroke-width="2"/>
                      </svg>
                      <span>{{ currNote.likeTotal }}</span>
                    </div>
                    <div class="flex items-center gap-1 cursor-pointer hover:text-gray-800">
                      <svg 
                        class="w-[20px] h-[20px] transition-all duration-200"
                        :class="[isNoteCollected ? 'animate-like' : 'animate-unlike']"
                        viewBox="0 0 24 24" 
                        :fill="isNoteCollected ? '#FF8C00' : 'none'" 
                        :stroke="isNoteCollected ? '#FF8C00' : 'currentColor'"
                        @click="handleNoteCollect"
                      >
                        <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      </svg>
                      <span>{{ currNote.collectTotal }}</span>
                    </div>
                    <div 
                      class="flex items-center gap-1 cursor-pointer hover:text-gray-800"
                      @click="focusComment"
                    >
                      <svg class="w-[20px] h-[20px]" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" stroke-width="2"/>
                      </svg>
                      <span class="text-sm">{{ currNote.commentTotal }}</span>
                    </div>
                  </div>
                </div>

                <!-- 输入框聚焦时显示的底部工具栏 -->
                <div v-if="isInputFocused" class="flex items-center justify-between mt-3">
                  <div class="flex items-center gap-1">
                    <div class="relative">
                      <button 
                        class="p-[10px] hover:text-[#333] hover:bg-gray-100 rounded-full"
                        @click="toggleEmojiPicker"
                        ref="emojiButtonRef"
                      >
                        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none">
                          <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="currentColor" stroke-width="2"/>
                          <path d="M8.5 15C8.5 15 9.8125 17 12 17C14.1875 17 15.5 15 15.5 15" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                          <path d="M9 10H9.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                          <path d="M15 10H15.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                        </svg>
                      </button>
                      
                      <!-- 表情选择弹出框 -->
                      <div 
                        v-if="showEmojiPicker" 
                        class="emoji-picker border border-gray-200"
                        ref="emojiPickerRef"
                      >
                        <div class="emoji-grid">
                          <button 
                            v-for="emoji in emojiList" 
                            :key="emoji"
                            class="emoji-item"
                            @click="insertEmoji(emoji)"
                          >
                            {{ emoji }}
                          </button>
                        </div>
                      </div>
                    </div>
                    
                    <!-- 上传图片按钮 -->
                    <div class="relative">
                      <button 
                        class="p-[10px] hover:text-[#333] hover:bg-gray-100 rounded-full"
                        @click="triggerFileUpload"
                      >
                        <svg class="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                          <path d="M19 3H5C3.89543 3 3 3.89543 3 5V19C3 20.1046 3.89543 21 5 21H19C20.1046 21 21 20.1046 21 19V5C21 3.89543 20.1046 3 19 3Z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          <path d="M8.5 10C9.32843 10 10 9.32843 10 8.5C10 7.67157 9.32843 7 8.5 7C7.67157 7 7 7.67157 7 8.5C7 9.32843 7.67157 10 8.5 10Z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          <path d="M21 15L16 10L5 21" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                      </button>
                      <input 
                        type="file" 
                        ref="fileInputRef" 
                        class="hidden" 
                        accept="image/*"
                        @change="handleFileChange"
                      />
                    </div>
                  </div>
                  <div class="flex items-center gap-2">
                    <!-- 发送按钮 -->
                    <button 
                      class="w-[64px] h-[40px] text-[16px] text-white bg-[#ff2442] 
                      rounded-full font-bold cursor-pointer"
                      :class="{'opacity-50': !commentContent.trim() && !commentImage}"
                      @click="handlePublishComment"
                    >
                      发送
                    </button>
                    <button class="border border-gray-200 w-[64px] h-[40px] text-[16px] 
                    font-bold text-gray-600 hover:text-gray-800 hover:bg-gray-100 
                    rounded-full cursor-pointer" @click="onCancel">
                      取消
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, computed, nextTick, watch, onBeforeUnmount, inject, onMounted } from 'vue'
import gsap from 'gsap'
import CommentList from './CommentList.vue'
import ImageCarousel from '@/components/common/ImageCarousel.vue'
import VideoPlayer from '@/components/common/VideoPlayer.vue'
import { getNoteDetail, likeNote, unlikeNote, collectNote, uncollectNote, isLikedAndCollectedData } from '@/api/note' // 获取笔记详情的API
import { getCommentList, publishComment, getChildCommentList, likeComment, unlikeComment } from '@/api/comment'
import { followUser } from '@/api/relation'
import { useUserStore } from '@/stores/user'
import { message } from '@/utils/message'
import { uploadFile } from '@/api/file' // 导入文件上传API

const userStore = useUserStore()

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  note: {
    type: Object,
    default: () => ({})
  }
})

const currNote = ref({})
const currNoteId = ref('')

const emit = defineEmits(['update:visible'])

// DOM 引用
const modalRef = ref(null)
const authorInfoRef = ref(null)
const contentRef = ref(null)
const scrollContainerRef = ref(null)

// 动画相关状态
let animation = null

// 在组件卸载前清除所有动画
onBeforeUnmount(() => {
  if (animation) {
    animation.kill()
    animation = null
  }
})

// 关闭模态框
const onClose = () => {
  emit('update:visible', false)
}

// 动画相关方法
const onBeforeEnter = (el) => {
  if (modalRef.value) {
    gsap.set(modalRef.value, {
      scale: 0.8,
      opacity: 0
    })
  }
}

const onEnter = (el, done) => {
  nextTick(() => {
    if (modalRef.value) {
      animation = gsap.to(modalRef.value, {
        scale: 1,
        opacity: 1,
        duration: 0.3,
        ease: 'back.out(1.7)',
        onComplete: done
      })
    } else {
      done()
    }
  })
}

const onLeave = (el, done) => {
  if (modalRef.value) {
    animation = gsap.to(modalRef.value, {
      scale: 0.8,
      opacity: 0,
      duration: 0.2,
      ease: 'power1.in',
      onComplete: done
    })
  } else {
    done()
  }
}

const isScrolled = ref(false)

const handleScroll = (e) => {
  // 设置 isScrolled 状态
  isScrolled.value = e.target.scrollTop > 0
  
  const container = e.target
  const scrollTop = container.scrollTop
  const scrollHeight = container.scrollHeight
  const clientHeight = container.clientHeight

  // 当滚动到距离底部 50px 时触发加载
  if (scrollHeight - scrollTop - clientHeight < 50) {
    console.log('已经滚动到最后一条评论，准备加载下一页数据...')
    loadMoreComments()
  }
}

const currCommentPageNo = ref(1)
const totalCommentPage = ref(0)
const comments = ref([])


const commentTotal = ref(0)
const hasMoreComments = computed(() => currCommentPageNo.value < totalCommentPage.value)
const moreCommentsCount = ref(7)

// 加载更多评论
const isLoadingMoreComments = ref(false)

const loadMoreComments = () => {
  console.log('加载更多评论')
  if (currCommentPageNo.value >= totalCommentPage.value || isLoadingMoreComments.value) return
  
  isLoadingMoreComments.value = true
  const nextPage = currCommentPageNo.value + 1
  
  getCommentList(currNoteId.value, nextPage).then(res => {
    console.log('加载更多评论结果:', res)
    if (res.success) {
      // 过滤掉可能重复的评论
      const existingCommentIds = new Set(comments.value.map(c => c.commentId))
      const newComments = res.data.filter(c => !existingCommentIds.has(c.commentId))
      
      // 将新评论追加到现有列表
      comments.value = [...comments.value, ...newComments]
      currCommentPageNo.value = res.pageNo
      commentTotal.value = res.totalCount
      totalCommentPage.value = res.totalPage
    }
  }).finally(() => {
    isLoadingMoreComments.value = false
  })
}

// 登录状态控制
const isLoggedIn = computed(() => !!userStore.token)

// 评论输入框状态
const isInputFocused = ref(false)
const commentInput = ref(null)
const commentContent = ref('')

// 添加回复对象状态
const replyTo = ref(null)

const showLoginModal = inject('showLoginModal')

// 聚焦评论输入框
const focusComment = () => {
  if (!isLoggedIn.value) {
    showLoginModal.value = true
    return
  }
  isInputFocused.value = true
  nextTick(() => {
    if (commentInput.value) {
      commentInput.value.focus()
    }
  })
}

// 修改回复点击处理
const onReplyClick = (comment) => {
  console.log('回复点击', comment)
  // 如果是二级评论，需要找到其父评论
  if (comment.isReply) {
    const parentComment = comments.value.find(c => 
      c.replies?.some(r => r.id === comment.id)
    )
    if (parentComment) {
      replyTo.value = comment
      isInputFocused.value = true
      nextTick(() => {
        if (commentInput.value) {
          commentInput.value.focus()
        }
      })
    }
  } else {
    replyTo.value = comment
    isInputFocused.value = true
    nextTick(() => {
      if (commentInput.value) {
        commentInput.value.focus()
      }
    })
  }
}

// 清除回复
const clearReply = () => {
  replyTo.value = null
}

// 输入框失焦处理
const onInputBlur = (e) => {
  // 只有点击取消按钮时才会关闭输入框
  if (e.relatedTarget?.textContent === '取消') {
    isInputFocused.value = false
  }
}

// 监听评论内容
const isCommentEmpty = computed(() => !commentContent.value.trim())

// 评论图片相关
const commentImage = ref('')
const fileInputRef = ref(null)

// 修改取消评论处理
const onCancel = () => {
  isInputFocused.value = false
  commentContent.value = ''
  commentImage.value = '' // 清除已上传的图片
  replyTo.value = null  // 清除回复对象
  if (commentInput.value) {
    commentInput.value.blur()
  }
}

// 监听模态框可见性变化
watch(() => props.visible, (newVisible) => {
  if (newVisible && props.note && props.note.id) {
    // 模态框打开时加载数据
    currNoteId.value = props.note.id
    currNote.value = { ...props.note }
    
    // 加载笔记详情
    getNoteDetail(props.note.id).then(res => {
      if (res.success) {
        currNote.value = res.data
      }
    })
    
    // 加载评论列表第一页
    getCommentList(props.note.id, 1).then(res => {
      if (res.success) {
        comments.value = res.data
        commentTotal.value = res.totalCount
        currCommentPageNo.value = res.pageNo
        totalCommentPage.value = res.totalPage
        hasMoreComments.value = res.pageNo < res.totalPage
      }
    })

    isLikedAndCollectedData(props.note.id).then(res => {
      if (res.success) {
        isNoteLiked.value = res.data.isLiked
        isNoteCollected.value = res.data.isCollected
      }
    })
  } else {
    // 模态框关闭时重置数据
    currNote.value = {}
    currNoteId.value = ''
    comments.value = []
    commentTotal.value = 0
    currCommentPageNo.value = 1
    totalCommentPage.value = 1
    hasMoreComments.value = false
    commentContent.value = ''
    commentImage.value = ''
    replyTo.value = null
    isInputFocused.value = false
    isScrolled.value = false
    isNoteLiked.value = false
    isNoteCollected.value = false
  }
})

// 表情选择相关
const showEmojiPicker = ref(false)
const emojiButtonRef = ref(null)
const emojiPickerRef = ref(null)

// 常用表情列表
const emojiList = [
  '😀', '😃', '😄', '😁', '😆', '😅', '😂', '🤣', '😊', '😇',
  '🙂', '🙃', '😉', '😌', '😍', '🥰', '😘', '😗', '😙', '😚',
  '😋', '😛', '😝', '😜', '🤪', '🤨', '🧐', '🤓', '😎', '🤩',
  '🥳', '😏', '😒', '😞', '😔', '😟', '😕', '🙁', '☹️', '😣',
  '😖', '😫', '😩', '🥺', '😢', '😭', '😤', '😠', '😡', '🤬',
  '🤯', '😳', '🥵', '🥶', '😱', '😨', '😰', '😥', '😓', '🤗',
  '🤔', '🤭', '🤫', '🤥', '😶', '😐', '😑', '😬', '🙄', '😯',
  '😦', '😧', '😮', '😲', '🥱', '😴', '🤤', '😪', '😵', '🤐',
  '🥴', '🤢', '🤮', '🤧', '😷', '🤒', '🤕', '🤑', '🤠', '😈',
  '👿', '👹', '👺', '🤡', '💩', '👻', '💀', '☠️', '👽', '👾'
]

// 切换表情选择器显示状态
const toggleEmojiPicker = () => {
  showEmojiPicker.value = !showEmojiPicker.value
}

// 插入表情到评论内容
const insertEmoji = (emoji) => {
  commentContent.value += emoji
  // 选中表情后隐藏表情选择器
  showEmojiPicker.value = false
}

// 点击外部关闭表情选择器
const handleClickOutside = (event) => {
  if (
    showEmojiPicker.value && 
    emojiPickerRef.value && 
    !emojiPickerRef.value.contains(event.target) &&
    !emojiButtonRef.value.contains(event.target)
  ) {
    showEmojiPicker.value = false
  }
}

// 组件挂载时添加点击外部关闭事件
onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

// 组件卸载时移除事件监听
onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})



// 触发文件选择
const triggerFileUpload = () => {
  fileInputRef.value.click()
}

// 处理文件选择
const handleFileChange = (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  // 检查文件类型
  if (!file.type.startsWith('image/')) {
    message.show('请选择图片文件')
    return
  }
  
  // 检查文件大小（限制为5MB）
  if (file.size > 5 * 1024 * 1024) {
    message.show('图片大小不能超过5MB')
    return
  }
  
  // 上传文件
  const formData = new FormData()
  formData.append('file', file)
  
  message.show('图片上传中...')
  
  uploadFile(formData).then(res => {
    if (res.success) {
      commentImage.value = res.data
    } else {
      message.show('图片上传失败')
    }
  }).catch(err => {
    console.error('图片上传错误:', err)
    message.show('图片上传失败')
  })
  
  // 重置文件输入，以便可以再次选择同一文件
  event.target.value = ''
}

// 移除已上传的图片
const removeImage = () => {
  commentImage.value = ''
}

// 在评论列表中查找指定评论ID的评论的父评论
const findParentComment = (commentId, commentsList) => {
  for (const comment of commentsList) {
    // 检查一级评论的子评论
    if (comment.childComments) {
      const childIndex = comment.childComments.findIndex(child => child.commentId === commentId)
      if (childIndex !== -1) {
        return { parentComment: comment, isChild: true, childIndex }
      }
    }
    // 检查一级评论
    if (comment.commentId === commentId) {
      return { parentComment: comment, isChild: false }
    }
  }
  return null
}

// 修改发布评论函数
const handlePublishComment = () => {
  console.log('发布评论, ' + currNoteId.value)
  
  // 检查是否有内容或图片
  if (!commentContent.value.trim() && !commentImage.value) {
    message.show('请输入评论内容或上传图片')
    return
  }
  
  publishComment({
    noteId: currNoteId.value,
    content: commentContent.value,
    replyCommentId: replyTo.value?.commentId,
    imageUrl: commentImage.value
  }).then(res => {
    if (res.success) {
      message.show('评论成功')
      
      let commentId = res.data || null

      // 构建新评论对象
      const newComment = {
        commentId: commentId,
        content: commentContent.value,
        createTime: '刚刚',
        nickname: userStore.profile.nickname,
        avatar: userStore.profile.avatar,
        likeTotal: 0,
        imageUrl: commentImage.value,
        isNewComment: true  // 添加新评论标识
      }
      
      // 判断是否为回复评论
      if (replyTo.value && replyTo.value.commentId) {
        // 查找被回复评论的父评论
        const result = findParentComment(replyTo.value.commentId, comments.value)
        if (result) {
          if (result.isChild) {
            // 如果回复的是二级评论，将新评论插入到同级的后面
            result.parentComment.childComments.splice(result.childIndex + 1, 0, newComment)
          } else {
            // 如果回复的是一级评论，添加到其子评论列表
            if (!result.parentComment.childComments) {
              result.parentComment.childComments = []
            }
            // 确保 childCommentTotal 正确更新
            if (!result.parentComment.childCommentTotal) {
              result.parentComment.childCommentTotal = 0
            }
            result.parentComment.childCommentTotal += 1
            
            // 如果还没有加载过子评论或只有默认的一条，直接添加到数组中
            if (!result.parentComment.childComments.length) {
              result.parentComment.childComments = [newComment]
            } else {
              // 如果已经加载了子评论，添加到开头
              result.parentComment.childComments.unshift(newComment)
            }
          }
        }
      } else {
        // 是一级评论，添加到评论列表最前面
        if (comments.value && comments.value.length > 0) {
          comments.value = [newComment, ...comments.value]
        } else {
          comments.value = [newComment]
        }
      }
      
      // 更新评论总数
      commentTotal.value += 1
      
      // 重置输入框和状态
      isInputFocused.value = false
      commentContent.value = ''
      commentImage.value = '' // 清除已上传的图片
      if (commentInput.value) {
        commentInput.value.blur()
      }
      
      // 如果是回复评论，滚动到父评论位置
      // 如果是一级评论，滚动到评论区顶部
      nextTick(() => {
        if (scrollContainerRef.value) {
          // 只有发布一级评论（直接评论笔记）时才滚动到评论区顶部
          if (!replyTo.value) {
            console.log('一级评论发布成功后需要滚动到评论区顶部')
            const contentHeight = contentRef.value ? contentRef.value.offsetHeight : 0
            scrollContainerRef.value.scrollTop = contentHeight
          } else {
            console.log('二级评论发布成功后不需要滚动，保持当前位置即可')
            // 二级评论发布成功后不需要滚动，保持当前位置即可
          }
          replyTo.value = null  // 清除回复对象
        }
      })
    }
  })
}

// 加载二级评论
const loadChildComments = (parentComment, pageNo = 1) => {
  if (!parentComment || !parentComment.commentId) return
  
  // 确保父评论有 childComments 数组和分页信息
  if (!parentComment.childComments) {
    parentComment.childComments = []
  }
  if (!parentComment.currChildCommentPage) {
    parentComment.currChildCommentPage = 0
  }
  
  getChildCommentList(parentComment.commentId, parentComment.currChildCommentPage + 1).then(res => {
    if (res.success) {
      if (res.data && res.data.length > 0) {
        // 有数据时，将新的子评论追加到现有列表末尾
        parentComment.childComments.push(...res.data)
        
        // 更新分页信息
        parentComment.childCommentTotal = res.totalCount
        parentComment.currChildCommentPage = res.pageNo
        parentComment.totalChildCommentPage = res.totalPage
        parentComment.hasMoreChildComments = res.pageNo < res.totalPage
      } else {
        // 如果返回的数据为空，标记为没有更多评论
        parentComment.hasMoreChildComments = false
      }
    }
  })
}

// 处理展开回复事件
const handleExpandReplies = (comment) => {
  console.log('展开评论的回复列表:', comment)
  loadChildComments(comment)
}

// 添加点赞状态
const isNoteLiked = ref(false)
// 处理笔记点赞、取消点赞
const handleNoteLike = () => {
  if (!isLoggedIn.value) {
    showLoginModal.value = true
    return
  }

  if (!isNoteLiked.value) {
    likeNote(currNoteId.value).then(res => {
    if (res.success) {
      console.log('点赞成功')
      isNoteLiked.value = !isNoteLiked.value
      currNote.value.likeTotal++
      } else {
        message.show(res.message)
      }
    })
    return
  }
  
  unlikeNote(currNoteId.value).then(res => {
    if (res.success) {
      console.log('取消点赞成功')
      isNoteLiked.value = !isNoteLiked.value
      currNote.value.likeTotal--
    }
  })
}

// 添加评论点赞处理函数
const handleCommentLike = ({ comment, liked }) => {


  console.log('评论点赞:', comment.commentId, liked)
  if (liked) {
    likeComment(comment.commentId).then(res => {
    if (res.success) {
      console.log('点赞成功')
      // 直接更新传入的 comment 对象的点赞数
      comment.likeTotal++
      } else {
        message.show(res.message)
      }
    })
    return
  }
  
  unlikeComment(comment.commentId).then(res => {
    if (res.success) {
      console.log('取消点赞成功')
      comment.likeTotal--
    }
  })
}

// 添加收藏状态
const isNoteCollected = ref(false)

// 处理笔记收藏
const handleNoteCollect = () => {
  if (!isLoggedIn.value) {
    showLoginModal.value = true
    return
  }
  if (!isNoteCollected.value) {
    collectNote(currNoteId.value).then(res => {
      if (res.success) {
        console.log('收藏成功')
        isNoteCollected.value = !isNoteCollected.value
        currNote.value.collectTotal++
      } else {
        message.show(res.message)
      }
    })
    return
  }

  uncollectNote(currNoteId.value).then(res => {
    if (res.success) {
      console.log('取消收藏成功')
      isNoteCollected.value = !isNoteCollected.value
      currNote.value.collectTotal--
    }
  })
}

const handleFollow = () => {
  console.log('关注用户:', currNote.value.creatorId)
  followUser(currNote.value.creatorId).then(res => {
    if (!res.success) {
      message.show(res.message)
      return
    }
    message.show('关注成功')
  })
}
</script>

<style scoped>
.zoom-move {
  transition: transform 0.3s ease-out;
}

/* 防止图片溢出容器 */
img {
  max-height: 90vh;
  width: auto;
}

.title {
    margin-bottom: 8px;
    font-weight: 600;
    font-size: 18px;
    line-height: 140%;
}

.content-input {
  caret-color: #ff2442;
  margin: 0px;
  height: 40px;  /* 固定高度 */
  background-color: rgba(0, 0, 0, 0.03);
  border: none;
  padding: 0 10px;  /* 调整内边距 */
  border-radius: 20px;
  outline: none;
  display: flex;
  align-items: center;
  white-space: nowrap;  /* 防止换行 */
}

/* 未聚焦状态下隐藏滚动条 */
.content-input:not(:focus-within) {
  overflow: hidden;
}

/* 限制回复内容显示一行 */
.line-clamp-1 {
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
}

.reply {
    color: rgba(51, 51, 51, 0.6);
    font-size: 14px;
}

.reply-content {
    color: rgba(51, 51, 51, 0.8);
    font-size: 14px;
    width: 100%;
    margin-top: 4px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

/* 隐藏输入框的默认 placeholder */
input::placeholder {
    color: transparent;
}

/* 聚焦时显示 placeholder */
input:focus::placeholder {
    color: rgba(51, 51, 51, 0.6);
}

/* 修改图片样式，确保图片适应容器 */
:deep(.carousel-container) {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

:deep(.carousel-image) {
  max-width: 100%;
  max-height: 90vh;
  object-fit: contain;
  object-position: center;
}

/* 表情选择器样式 */
.emoji-picker {
  position: absolute;
  bottom: 45px;
  left: 0;
  max-height: 280px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  padding: 10px;
  z-index: 100;
  overflow-y: auto;
}

.emoji-grid {
  display: grid;
  grid-template-columns: repeat(10, 1fr);
  gap: 5px;
}

.emoji-item {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  font-size: 28px;
  cursor: pointer;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.emoji-item:hover {
  background-color: #f5f5f5;
}

/* 点赞动画效果 */
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
</style> 