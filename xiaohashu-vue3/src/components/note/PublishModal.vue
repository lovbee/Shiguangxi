<template>
  <Teleport to="body">
    <!-- 遮罩层 - 调整透明度和模糊效果 -->
    <div v-if="visible" class="fixed inset-0 bg-gray-800/25 backdrop-blur-sm z-[100]"></div>
    
    <Transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="transform scale-95 opacity-0"
      enter-to-class="transform scale-100 opacity-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="transform scale-100 opacity-100"
      leave-to-class="transform scale-95 opacity-0"
    >
      <!-- 发布笔记模态框 -->
      <div v-if="visible" class="fixed inset-0 z-[101] flex items-center justify-center p-4">
        <div class="bg-white w-[800px] rounded-lg flex flex-col max-h-[90vh] shadow-2xl">
          <!-- 顶部标题栏 - 优化间距和分割线 -->
          <div class="p-[24px] flex items-center justify-between px-8 border-b border-gray-100/60 shrink-0">
            <h2 class="text-[18px] font-bold tracking-tight text-gray-800">发布笔记</h2>
            <button 
              class="w-8 h-8 flex items-center justify-center hover:bg-gray-100/80 rounded-full transition-colors"
              @click="onClose"
            >
              <svg class="w-5 h-5 text-gray-500" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M18 6L6 18M6 6l12 12" stroke-width="2" stroke-linecap="round"/>
              </svg>
            </button>
          </div>

          <!-- 内容区域 - 优化内边距和间距 -->
          <div class="flex-1 overflow-auto px-8 py-6 min-h-[500px]">
            <!-- 笔记类型选择 -->
            <div class="mb-6 border-b border-gray-100 pb-4">
              <div class="text-sm font-medium text-gray-700 mb-3">笔记类型</div>
              <div class="flex gap-4">
                <button 
                  class="px-4 py-2 rounded-full text-sm font-medium transition-colors border"
                  :class="noteType === 'image' 
                    ? 'border-[#ff2442] text-[#ff2442] bg-[#fff5f7]' 
                    : 'border-gray-200 text-gray-700 hover:border-gray-300 bg-white'"
                  @click="setNoteType('image')"
                >
                  <div class="flex items-center">
                    <svg class="w-4 h-4 mr-1.5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <rect x="3" y="3" width="18" height="18" rx="2" stroke-width="2"/>
                      <circle cx="8.5" cy="8.5" r="1.5" fill="currentColor"/>
                      <path d="M21 15l-5-5L5 21" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    图文
                    <!-- 对号标识 -->
                    <svg 
                      v-if="noteType === 'image'" 
                      class="w-4 h-4 ml-1.5 text-[#ff2442]" 
                      viewBox="0 0 24 24" 
                      fill="none" 
                      stroke="currentColor"
                    >
                      <path d="M20 6L9 17l-5-5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </div>
                </button>
                <button 
                  class="px-4 py-2 rounded-full text-sm font-medium transition-colors border"
                  :class="noteType === 'video' 
                    ? 'border-[#ff2442] text-[#ff2442] bg-[#fff5f7]' 
                    : 'border-gray-200 text-gray-700 hover:border-gray-300 bg-white'"
                  @click="setNoteType('video')"
                >
                  <div class="flex items-center">
                    <svg class="w-4 h-4 mr-1.5" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <rect x="2" y="2" width="20" height="20" rx="2.18" stroke-width="2"/>
                      <path d="M10 8l6 4-6 4V8z" fill="currentColor"/>
                    </svg>
                    视频
                    <!-- 对号标识 -->
                    <svg 
                      v-if="noteType === 'video'" 
                      class="w-4 h-4 ml-1.5 text-[#ff2442]" 
                      viewBox="0 0 24 24" 
                      fill="none" 
                      stroke="currentColor"
                    >
                      <path d="M20 6L9 17l-5-5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </div>
                </button>
              </div>
            </div>

            <!-- 图片/视频上传区域 -->
            <div class="flex gap-4 overflow-x-auto pb-4 -mx-1 px-1">
              <!-- 已上传图片/视频预览 -->
              <div 
                v-for="(file, index) in files" 
                :key="index"
                class="relative w-[135px] h-[135px] rounded-xl overflow-hidden bg-gray-100 shrink-0 border border-gray-200"
                :class="{
                  'opacity-50': draggedItem === index,
                  'border-[#ff2442] border-2': dragOverIndex === index && draggedItem !== index,
                  'cursor-grab': !isVideo
                }"
                :draggable="!isVideo"
                @dragstart="startDrag(index)"
                @dragend="endDrag"
                @dragenter="onDragEnter(index)"
                @dragleave="onDragLeave"
                @dragover="onDragOver"
                @drop="onDrop(index)"
              >
                <!-- 上传中状态 -->
                <div 
                  v-if="isUploading && index >= files.length - (noteType === 'video' ? 1 : files.length)"
                  class="absolute inset-0 bg-black/30 backdrop-blur-sm flex flex-col items-center justify-center text-white"
                >
                  <svg class="animate-spin h-8 w-8 mb-2" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" fill="currentColor"></path>
                  </svg>
                  <div class="text-sm">上传中 {{ uploadProgress }}%</div>
                </div>
                
                <!-- 视频缩略图 -->
                <div 
                  v-if="isVideo && file.type.startsWith('video/')"
                  class="w-full h-full relative cursor-zoom-in"
                  @click="previewImage(index)"
                >
                  <video 
                    :src="getPreviewUrl(file)" 
                    class="w-full h-full object-cover"
                    muted
                  ></video>
                  <!-- 播放按钮覆盖层 -->
                  <div class="absolute inset-0 flex items-center justify-center bg-black/20 hover:bg-black/30 transition-colors">
                    <div class="w-10 h-10 rounded-full bg-white/80 backdrop-blur-sm flex items-center justify-center">
                      <svg class="w-5 h-5 text-[#ff2442]" viewBox="0 0 24 24" fill="currentColor" stroke="none">
                        <path d="M8 5v14l11-7z"/>
                      </svg>
                    </div>
                  </div>
                </div>
                
                <!-- 图片预览 -->
                <img 
                  v-else
                  :src="getPreviewUrl(file)" 
                  class="w-full h-full object-cover cursor-zoom-in"
                  @click="previewImage(index)"
                />
                <button 
                  class="absolute right-2 top-2 w-7 h-7 rounded-full bg-black/50 backdrop-blur-sm flex items-center justify-center hover:bg-black/60 transition-colors"
                  @click.stop="removeFile(index)"
                >
                  <svg class="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M18 6L6 18M6 6l12 12" stroke-width="2" stroke-linecap="round"/>
                  </svg>
                </button>
                
                <!-- 拖拽提示图标 - 只在图文模式下显示 -->
                <div 
                  v-if="!isVideo && files.length > 1"
                  class="absolute left-2 top-2 w-7 h-7 rounded-full bg-black/50 backdrop-blur-sm flex items-center justify-center"
                >
                  <svg class="w-4 h-4 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M8 9h8M8 15h8" stroke-width="2" stroke-linecap="round"/>
                  </svg>
                </div>
                
                <!-- 图片序号 -->
                <div 
                  v-if="!isVideo"
                  class="absolute left-2 bottom-2 w-6 h-6 rounded-full bg-black/50 backdrop-blur-sm flex items-center justify-center text-white text-xs font-medium"
                >
                  {{ index + 1 }}
                </div>
              </div>

              <!-- 上传按钮 -->
              <div 
                v-if="(noteType === 'image' && files.length < 8) || (noteType === 'video' && files.length === 0)"
                class="w-[135px] h-[135px] rounded-xl border-2 border-dashed border-gray-200 flex flex-col items-center 
                justify-center cursor-pointer hover:border-[#ff2442] hover:bg-gray-100 transition-colors bg-gray-50/50 shrink-0"
                @click="triggerUpload"
                :class="{'opacity-50 pointer-events-none': isUploading}"
              >
                <input 
                  type="file" 
                  ref="fileInput"
                  class="hidden"
                  :accept="noteType === 'image' ? 'image/*' : 'video/*'"
                  :multiple="noteType === 'image'"
                  @change="handleFileChange"
                />
                <div class="w-10 h-10 rounded-full bg-white mb-2 flex items-center justify-center border border-gray-200">
                  <svg class="w-5 h-5 text-[#ff2442]" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                    <path d="M12 5v14M5 12h14" stroke-width="2" stroke-linecap="round"/>
                  </svg>
                </div>
                <div class="text-[13px] text-gray-500 font-medium">
                  {{ isUploading ? '上传中...' : (noteType === 'image' ? `${files.length}/8` : '上传视频') }}
                </div>
              </div>
            </div>

            <!-- 拖拽提示 - 只在图文模式下且有多张图片时显示 -->
            <div 
              v-if="!isVideo && files.length > 1"
              class="text-[13px] text-gray-500 mt-1 flex items-center"
            >
              <svg class="w-4 h-4 mr-1 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path d="M12 5v14M5 12h14" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              拖拽可调整图片顺序
            </div>

            <!-- 图片/视频必填提示 -->
            <div 
              v-if="errors.files" 
              class="text-[#ff2442] text-[13px] mt-1 flex items-center"
            >
              <svg class="w-3.5 h-3.5 mr-1" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <circle cx="12" cy="12" r="10" stroke-width="2"/>
                <path d="M12 8v4M12 16h.01" stroke-width="2" stroke-linecap="round"/>
              </svg>
              {{ noteType === 'image' ? '请上传至少一张图片' : '请上传一个视频' }}
            </div>

            <!-- 标题输入 -->
            <div class="relative mt-2">
              <div class="relative">
                <input 
                  type="text"
                  v-model="title"
                  placeholder="填写标题，可能会帮助更多人看到你的笔记"
                  class="w-full text-[14px] py-4 focus:outline-none border-b border-gray-100 placeholder:text-gray-400 transition-colors pr-20"
                  :class="{'border-[#ff2442]': errors.title}"
                />
                <!-- 清除按钮和字数统计 -->
                <div class="absolute right-0 top-1/2 -translate-y-1/2 flex items-center gap-2">
                  <button 
                    v-if="title"
                    class="w-4 h-4 flex items-center justify-center text-gray-400 hover:text-gray-600"
                    @click="title = ''"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <circle cx="12" cy="12" r="10" stroke-width="2"/>
                      <path d="M15 9l-6 6M9 9l6 6" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                  </button>
                  <span class="text-[13px] text-gray-400 font-medium">{{ title.length }}/20</span>
                </div>
              </div>
              <!-- 标题必填提示 -->
              <div 
                v-if="errors.title" 
                class="text-[#ff2442] text-[13px] mt-1 flex items-center"
              >
                <svg class="w-3.5 h-3.5 mr-1" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                  <circle cx="12" cy="12" r="10" stroke-width="2"/>
                  <path d="M12 8v4M12 16h.01" stroke-width="2" stroke-linecap="round"/>
                </svg>
                请填写标题
              </div>
            </div>

            <!-- 正文输入 -->
            <div class="relative mt-2">
              <div class="relative">
                <textarea 
                  v-model="content"
                  placeholder="添加正文"
                  rows="6"
                  class="w-full text-[14px] py-4 focus:outline-none resize-none placeholder:text-gray-400 pr-20"
                ></textarea>
                <!-- 清除按钮和字数统计 -->
                <div class="absolute right-0 bottom-2 flex items-center gap-2">
                  <button 
                    v-if="content"
                    class="w-4 h-4 flex items-center justify-center text-gray-400 hover:text-gray-600"
                    @click="content = ''"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <circle cx="12" cy="12" r="10" stroke-width="2"/>
                      <path d="M15 9l-6 6M9 9l6 6" stroke-width="2" stroke-linecap="round"/>
                    </svg>
                  </button>
                  <span class="text-[13px] text-gray-400 font-medium">{{ content.length }}/1000</span>
                </div>
              </div>
            </div>

            <!-- 底部选项区域 -->
            <div class="space-y-2 mt-4">
              <!-- 选择频道 -->
              <div class="relative border-t border-gray-100">
                <div 
                  class="relative py-4 px-4 mt-2 -mx-4 cursor-pointer hover:bg-gray-100 rounded-lg flex items-center justify-between"
                  @click="showChannelSelector = !showChannelSelector"
                  ref="channelTriggerRef"
                >
                  <div class="flex items-center text-[14px] text-[#333]">
                    <svg class="w-4 h-4 mr-3 text-gray-500" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path d="M4 4h6v6H4V4zm10 0h6v6h-6V4zM4 14h6v6H4v-6zm10 0h6v6h-6v-6z" stroke-width="2"/>
                    </svg>
                    <span>
                      {{ selectedChannel ? selectedChannel.name : '选择频道' }}
                    </span>
                  </div>
                  <svg 
                    class="w-4 h-4 text-gray-400 transition-transform duration-200"
                    :class="{'rotate-90': showChannelSelector}"
                    viewBox="0 0 24 24" 
                    fill="none" 
                    stroke="currentColor"
                  >
                    <path d="M9 18l6-6-6-6" stroke-width="2" stroke-linecap="round"/>
                  </svg>
                </div>

                <!-- 频道选择下拉框 -->
                <Transition
                  enter-active-class="transition duration-200"
                  enter-from-class="opacity-0 translate-y-2"
                  enter-to-class="opacity-100 translate-y-0"
                  leave-active-class="transition duration-200"
                  leave-from-class="opacity-100"
                  leave-to-class="opacity-0"
                >
                  <div 
                    v-if="showChannelSelector"
                    class="absolute bottom-full left-0 right-0 bg-white rounded-xl shadow-lg p-2 mb-2 z-20 border border-gray-200 channel-selector-dropdown"
                    ref="channelSelectorRef"
                  >
                    <div class="max-h-[300px] overflow-auto">
                      <button
                        v-for="channel in channelStore.channels"
                        :key="channel.id"
                        class="w-full px-4 py-3 rounded-xl text-left text-[14px] flex items-center justify-between hover:bg-gray-100 transition-colors"
                        :class="{'text-[#ff2442]': selectedChannel?.id === channel.id}"
                        @click="selectChannel(channel)"
                      >
                        <div class="flex items-center text-[#333]">
                          <component :is="channel.icon" class="w-4 h-4 mr-2"/>
                          {{ channel.name }}
                        </div>
                        <div v-if="selectedChannel?.id === channel.id" class="text-[#ff2442]">
                          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <path d="M20 6L9 17l-5-5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          </svg>
                        </div>
                      </button>
                    </div>
                  </div>
                </Transition>
              </div>

              <!-- 添加话题部分 -->
              <div class="relative border-t border-gray-100">
                <!-- 话题标题 -->
                <div class="py-4 px-4 -mx-4 mt-2">
                  <div class="flex items-center text-[14px] text-[#333] mb-3">
                    <svg class="w-4 h-4 mr-3 text-gray-500" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                      <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z" stroke-width="2"/>
                      <line x1="7" y1="7" x2="7.01" y2="7" stroke-width="2"/>
                    </svg>
                    <span>添加话题</span>
                  </div>
                  
                  <!-- 话题输入和已选话题 -->
                  <div class="relative">
                    <div class="flex flex-wrap items-center gap-2 min-h-[40px] p-2 border border-gray-200 rounded-lg focus-within:border-[#ff2442]">
                      <!-- 已选话题标签 -->
                      <div 
                        v-for="(topic, index) in selectedTopics" 
                        :key="index"
                        class="flex items-center bg-[#f5f5f5] text-[#333] px-2 py-1 rounded-full text-[13px]"
                      >
                        <span class="mr-1">#{{ topic.name }}</span>
                        <button 
                          class="w-4 h-4 flex items-center justify-center text-gray-500 hover:text-gray-700"
                          @click.stop="removeTopic(topic)"
                        >
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" class="w-3 h-3">
                            <path d="M18 6L6 18M6 6l12 12" stroke-width="2" stroke-linecap="round"/>
                          </svg>
                        </button>
                      </div>
                      
                      <!-- 话题输入框 -->
                      <input 
                        ref="topicInputRef"
                        v-model="topicKeyword"
                        type="text"
                        placeholder="添加话题，如：美食探店"
                        class="flex-1 min-w-[150px] outline-none text-[14px]"
                        @input="onTopicInput"
                        @keydown.enter.prevent="handleTopicEnter"
                        @keydown.backspace="handleTopicBackspace"
                        @focus="isTopicInputActive = true"
                        @blur="handleTopicBlur"
                        @click="isTopicInputActive = true"
                      />
                    </div>

                    <!-- 话题建议列表 -->
                    <div 
                      v-if="isTopicInputActive && (topicSuggestions.length > 0 || isLoadingTopics || topicKeyword.trim())"
                      class="absolute bottom-full left-0 right-0 bg-white rounded-xl shadow-lg p-2 mb-2 z-20 border border-gray-200 max-h-[300px] overflow-auto"
                    >
                      <!-- 加载中状态 -->
                      <div v-if="isLoadingTopics" class="py-3 px-4 text-gray-500 text-center">
                        <div class="flex items-center justify-center">
                          <svg class="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                            <path class="opacity-75" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" fill="currentColor"></path>
                          </svg>
                          正在搜索话题...
                        </div>
                      </div>
                      
                      <!-- 话题列表 -->
                      <button
                        v-for="topic in topicSuggestions"
                        :key="topic.id"
                        class="w-full px-4 py-3 rounded-xl text-left text-[14px] flex items-center hover:bg-gray-100 transition-colors"
                        @click="selectTopic(topic)"
                      >
                        <svg class="w-4 h-4 mr-2 text-gray-500" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                          <path d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                        <span class="text-[#333]">{{ topic.name }}</span>
                      </button>
                      
                      <!-- 添加新话题选项 -->
                      <button
                        v-if="topicKeyword.trim() && !isLoadingTopics && !isTopicExistsInSuggestions"
                        class="w-full px-4 py-3 rounded-xl text-left text-[14px] flex items-center justify-between hover:bg-gray-100 transition-colors"
                        @click="createNewTopic"
                      >
                        <div class="flex items-center">
                          <svg class="w-4 h-4 mr-2 text-gray-500" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                            <path d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                          </svg>
                          <span class="text-[#333]">{{ topicKeyword.trim() }}</span>
                        </div>
                        <span class="text-[#ff2442] text-xs font-medium">添加新话题</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 底部按钮区域 -->
          <div class="border-t border-gray-100 shrink-0">
            <div class="px-8 py-6 rounded-b-[20px] flex gap-4">
              <!-- 取消按钮 -->
              <button 
                class="w-32 border border-gray-200 text-gray-600 hover:text-gray-800 
                hover:bg-gray-100
                py-3 rounded-full font-bold text-[18px] cursor-pointer transition-all"
                @click="onClose"
              >
                取消
              </button>
              <!-- 发布按钮 -->
              <button 
                class="flex-1 bg-[#ff2442] text-white py-3 rounded-full font-bold text-[18px] hover:opacity-90 cursor-pointer transition-all"
                @click="handlePublish"
              >
                发布笔记
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- 图片预览组件 -->
    <ImagePreview
      v-model:visible="showImagePreview"
      :images="files.map(file => getPreviewUrl(file))"
      :initial-index="currentPreviewIndex"
    />
    
    <!-- 视频预览组件 -->
    <VideoPreview
      v-model:visible="showVideoPreview"
      :video-url="currentVideoUrl"
    />
  </Teleport>
</template>

<script setup>
import { 
  ref, 
  computed, 
  watch, 
  nextTick, 
  onMounted, 
  onUnmounted, 
  markRaw,
  defineComponent
} from 'vue'
import ImagePreview from '@/components/common/ImagePreview.vue'
import VideoPreview from '@/components/common/VideoPreview.vue'
import { useChannelStore } from '@/stores/channel'
import { getTopicList } from '@/api/topic'
import { uploadFile } from '@/api/file'
import { publishNote } from '@/api/note'
import { message } from '@/utils/message'
import { useRouter } from 'vue-router'

const router = useRouter()

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:visible'])

const channelStore = useChannelStore()

// 表单数据
const title = ref('')
const content = ref('')
const tags = ref('')
const files = ref([])
const isVideo = ref(false)
const fileInput = ref(null)

// 图片预览相关状态
const showImagePreview = ref(false)
const currentPreviewIndex = ref(0)
const showVideoPreview = ref(false)
const currentVideoUrl = ref('')

// 获取所有图片的预览URL
const previewUrls = computed(() => {
  return files.value.map(file => getPreviewUrl(file))
})

// 预览图片
const previewImage = (index) => {
  const file = files.value[index]
  
  if (file.type.startsWith('video/')) {
    // 视频预览
    currentVideoUrl.value = getPreviewUrl(file)
    showVideoPreview.value = true
  } else {
    // 图片预览
    currentPreviewIndex.value = index
    showImagePreview.value = true
  }
}

// 触发文件选择
const triggerUpload = () => {
  fileInput.value?.click()
}

// 笔记类型（图文/视频）
const noteType = ref('image') // 默认为图文类型

// 设置笔记类型
const setNoteType = (type) => {
  // 如果类型没有变化，不做任何处理
  if (noteType.value === type) return
  
  // 更新笔记类型
  noteType.value = type
  
  // 清空文件和URL数组
  files.value = []
  fileUrls.value = []
  
  // 重置视频标志
  isVideo.value = type === 'video'
  
  // 重置上传状态
  isUploading.value = false
  uploadProgress.value = 0
  
  // 重置文件相关错误
  if (errors.value.files) {
    errors.value.files = false
  }
}

// 文件相关状态
const fileUrls = ref([]) // 上传后的文件URL
const isUploading = ref(false) // 添加上传状态
const uploadProgress = ref(0) // 添加上传进度

// 处理文件选择
const handleFileChange = async (e) => {
  const selectedFiles = Array.from(e.target.files)
  if (!selectedFiles.length) return
  
  // 检查文件类型
  if (noteType.value === 'video') {
    if (!selectedFiles[0].type.startsWith('video/')) {
      message.show({ type: 'error', content: '请选择视频文件' })
      return
    }
    isVideo.value = true
    
    // 视频模式下，清空之前的文件和URL数组，确保一致性
    files.value = []
    fileUrls.value = []
  } else {
    // 图片模式下，过滤出图片文件
    const imageFiles = selectedFiles.filter(file => file.type.startsWith('image/'))
    if (imageFiles.length !== selectedFiles.length) {
      message.show({ type: 'error', content: '请只选择图片文件' })
      return
    }
    isVideo.value = false
  }
  
  // 限制文件数量
  let filesToAdd = []
  if (noteType.value === 'video') {
    // 视频模式下，只允许一个视频
    if (files.value.length === 0) {
      filesToAdd = [selectedFiles[0]]
    } else {
      message.show({ type: 'error', content: '只能上传一个视频' })
      return
    }
  } else {
    // 图片模式下，最多8张图片
    const remainingSlots = 8 - files.value.length
    if (remainingSlots <= 0) {
      message.show({ type: 'error', content: '最多只能上传8张图片' })
      return
    }
    filesToAdd = selectedFiles.slice(0, remainingSlots)
  }
  
  // 开始上传文件
  isUploading.value = true
  uploadProgress.value = 0
  
  try {
    // 添加到本地文件列表
    const newFiles = [...files.value, ...filesToAdd]
    files.value = newFiles
    
    // 逐个上传文件
    for (let i = 0; i < filesToAdd.length; i++) {
      const file = filesToAdd[i]
      
      // 更新上传进度
      uploadProgress.value = Math.round((i / filesToAdd.length) * 100)
      
      // 上传文件
      const formData = new FormData()
      formData.append('file', file)
      
      const res = await uploadFile(formData)
      
      if (res.success && res.data) {
        // 保存上传后的URL
        fileUrls.value.push(res.data)
      } else {
        console.error('文件上传失败:', res.message)
        // 从本地文件列表中移除上传失败的文件
        const index = files.value.indexOf(file)
        if (index !== -1) {
          files.value.splice(index, 1)
        }
        message.show({ 
          type: 'error', 
          content: `文件 ${file.name} 上传失败: ${res.message || '未知错误'}` 
        })
      }
    }
    
    // 上传完成
    uploadProgress.value = 100
    
    // 确保两个数组长度一致
    if (files.value.length > fileUrls.value.length) {
      // 如果不一致，调整files数组长度与fileUrls一致
      files.value = files.value.slice(0, fileUrls.value.length)
    }
    
    console.log('上传完成，文件数量:', files.value.length, '文件URL数量:', fileUrls.value.length)
  } catch (error) {
    console.error('文件上传出错:', error)
    message.show({ type: 'error', content: '文件上传出错，请重试' })
  } finally {
    isUploading.value = false
    // 重置文件输入框，允许重新选择相同文件
    e.target.value = ''
  }
}

// 移除文件
const removeFile = (index) => {
  // 同时移除本地文件和对应的URL
  files.value.splice(index, 1)
  fileUrls.value.splice(index, 1)
}

// 获取预览URL
const getPreviewUrl = (file) => {
  // 如果已经上传完成，使用上传后的URL
  const index = files.value.indexOf(file)
  if (index !== -1 && index < fileUrls.value.length) {
    return fileUrls.value[index]
  }
  
  // 否则使用本地URL
  return URL.createObjectURL(file)
}

// 监听输入并限制字数
watch(title, (newVal) => {
  if (newVal.length > 20) {
    title.value = newVal.slice(0, 20)
  }
})

watch(content, (newVal) => {
  if (newVal.length > 1000) {
    content.value = newVal.slice(0, 1000)
  }
})

// 修改表单验证
const isValid = computed(() => {
  return files.value.length > 0 && 
    title.value.trim() && 
    title.value.length <= 20 &&
    content.value.length <= 1000
})

// 话题相关状态
const isTopicInputActive = ref(false)
const topicKeyword = ref('')
const topicInputRef = ref(null)
const selectedTopics = ref([]) // 统一存储所有话题（已有话题和新话题）
const topicSuggestions = ref([])
const isLoadingTopics = ref(false)

// 直接处理话题输入，不使用防抖
const onTopicInput = async () => {
  try {
    // 确保输入框处于激活状态
    isTopicInputActive.value = true
    
    // 如果输入为空，清空建议并返回
    if (!topicKeyword.value.trim()) {
      topicSuggestions.value = []
      isLoadingTopics.value = false
      return
    }
    
    // 设置加载状态
    isLoadingTopics.value = true
    
    // 调用话题搜索接口
    const res = await getTopicList(topicKeyword.value.trim())
    console.log('话题搜索结果:', res) // 添加日志，帮助调试
    
    // 处理返回结果
    if (res.success && res.data) {
      // 过滤掉已选择的话题（包括已有话题和新话题）
      const selectedNames = selectedTopics.value.map(t => t.name.toLowerCase())
      
      topicSuggestions.value = res.data.filter(topic => 
        !selectedNames.includes(topic.name.toLowerCase())
      )
      
      console.log('过滤后的话题建议:', topicSuggestions.value) // 添加日志，帮助调试
    } else {
      console.log('获取话题列表:', res.message)
      topicSuggestions.value = []
    }
  } catch (error) {
    console.error('搜索话题失败:', error)
    topicSuggestions.value = []
  } finally {
    isLoadingTopics.value = false
  }
}

// 选择已有话题
const selectTopic = (topic) => {
  // 检查是否已经添加过相同的话题
  if (selectedTopics.value.some(t => t.name.toLowerCase() === topic.name.toLowerCase())) {
    return
  }
  
  // 添加到已选话题
  selectedTopics.value = [...selectedTopics.value, topic]
  topicKeyword.value = ''
  topicSuggestions.value = []
  
  // 选择话题后保持输入框激活状态
  isTopicInputActive.value = true
  
  // 选择话题后，让输入框重新获得焦点
  nextTick(() => {
    topicInputRef.value?.focus()
  })
}

// 创建新话题
const createNewTopic = () => {
  if (!topicKeyword.value.trim()) return
  
  const topicName = topicKeyword.value.trim()
  
  // 检查是否已经添加过相同的话题
  if (selectedTopics.value.some(t => t.name.toLowerCase() === topicName.toLowerCase())) {
    return
  }
  
  // 创建新话题对象
  const newTopic = {
    name: topicName,
    isNew: true // 标记为新话题
  }
  
  // 添加到已选话题
  selectedTopics.value = [...selectedTopics.value, newTopic]
  topicKeyword.value = ''
  topicSuggestions.value = []
  
  // 选择话题后保持输入框激活状态
  isTopicInputActive.value = true
  
  // 选择话题后，让输入框重新获得焦点
  nextTick(() => {
    topicInputRef.value?.focus()
  })
}

// 移除话题
const removeTopic = (topic) => {
  selectedTopics.value = selectedTopics.value.filter(t => t !== topic)
}

// 处理回车
const handleTopicEnter = () => {
  if (topicKeyword.value.trim()) {
    // 如果输入的话题已存在于建议列表中，选择该话题
    if (isTopicExistsInSuggestions.value) {
      const existingTopic = topicSuggestions.value.find(
        topic => topic.name.toLowerCase() === topicKeyword.value.trim().toLowerCase()
      )
      if (existingTopic) {
        selectTopic(existingTopic)
        return
      }
    }
    
    // 否则创建新话题
    createNewTopic()
  }
}

// 处理退格键
const handleTopicBackspace = (e) => {
  if (!topicKeyword.value && selectedTopics.value.length) {
    e.preventDefault()
    selectedTopics.value = selectedTopics.value.slice(0, -1)
  }
}

// 处理话题输入框失焦事件
const handleTopicBlur = () => {
  // 使用延时，以便在点击建议项时能够先执行点击事件
  setTimeout(() => {
    // 只有当不在输入状态时才关闭建议列表
    if (!topicKeyword.value.trim()) {
      isTopicInputActive.value = false
    }
  }, 200)
}

// 计算属性：检查当前输入的话题是否已存在于建议列表中
const isTopicExistsInSuggestions = computed(() => {
  if (!topicKeyword.value.trim()) return false
  
  const input = topicKeyword.value.trim().toLowerCase()
  return topicSuggestions.value.some(topic => 
    topic.name.toLowerCase() === input
  )
})

// 修改错误提示状态为对象
const errors = ref({
  title: false,
  files: false
})

// 频道相关状态
const showChannelSelector = ref(false)
const selectedChannel = ref(null)
const channelSelectorRef = ref(null)
const channelTriggerRef = ref(null)

// 添加选择频道的处理函数
const selectChannel = (channel) => {
  selectedChannel.value = channel
  showChannelSelector.value = false
}

// 修改点击外部关闭下拉框函数
const closeChannelSelector = (e) => {
  if (!showChannelSelector.value) return
  
  const target = e.target
  const selectorElement = channelSelectorRef.value
  const triggerElement = channelTriggerRef.value
  
  // 如果点击的不是选择器本身，也不是触发按钮，则关闭选择器
  if (selectorElement && 
      !selectorElement.contains(target) && 
      triggerElement && 
      !triggerElement.contains(target)) {
    showChannelSelector.value = false
  }
}

// 修改发布处理，对接后端接口
const handlePublish = async () => {
  // 重置错误状态
  errors.value = {
    title: !title.value.trim(),
    files: files.value.length === 0
  }
  
  // 如果有任何错误，阻止发布
  if (errors.value.title || errors.value.files) {
    return
  }
  
  // 检查字数限制
  if (title.value.length > 20 || content.value.length > 1000) {
    return
  }
  
  // 检查是否所有文件都已上传完成
  if (fileUrls.value.length !== files.value.length) {
    console.log('文件数量不匹配:', files.value.length, fileUrls.value.length)
    message.show({ type: 'warning', content: '文件正在上传中，请等待上传完成' })
    return
  }
  
  // 检查是否有文件URL
  if (fileUrls.value.length === 0) {
    message.show({ type: 'warning', content: '请上传文件' })
    return
  }
  
  // 检查是否选择了频道
  if (!selectedChannel.value) {
    message.show({ type: 'warning', content: '请选择频道' })
    return
  }
  
  try {
    // 准备话题数据
    // 对于已有话题，提交ID；对于新话题，提交名称字符串
    const topics = selectedTopics.value.map(topic => {
      return topic.id ? topic.id : topic.name
    })
    
    // 准备发布数据
    const noteData = {
      type: noteType.value === 'video' ? 1 : 0, // 0 图文，1视频
      title: title.value.trim(),
      content: content.value.trim(),
      channelId: selectedChannel.value.id,
      topics: topics
    }
    
    // 根据笔记类型添加不同的文件字段
    if (noteType.value === 'video') {
      // 视频笔记
      noteData.videoUri = fileUrls.value[0] // 只取第一个视频URL
    } else {
      // 图文笔记
      noteData.imgUris = fileUrls.value
    }
    
    console.log('发布笔记数据:', noteData)
    
    // 调用发布接口
    const res = await publishNote(noteData)
    
    if (res.success) {
      // 发布成功
      message.show('发布成功')
      onClose()
      router.push('/discover')
      location.reload()
    } else {
      // 发布失败
      message.show(res.message || '未知错误')
    }
  } catch (error) {
    console.error('发布笔记出错:', error)
    message.show('发布失败')
  }
}

// 修改关闭处理，重置所有状态
const onClose = () => {
  emit('update:visible', false)
  title.value = ''
  content.value = ''
  files.value = []
  fileUrls.value = [] // 清空文件URL
  isVideo.value = false
  noteType.value = 'image'
  isTopicInputActive.value = false
  topicKeyword.value = ''
  selectedTopics.value = []
  topicSuggestions.value = []
  // 重置所有错误状态
  errors.value = {
    title: false,
    files: false
  }
  selectedChannel.value = null
}

// 分别监听每个字段，只清除对应的错误
watch(title, () => {
  if (errors.value.title) {
    errors.value.title = false
  }
})

watch(files, () => {
  if (errors.value.files) {
    errors.value.files = false
  }
})

// 处理 ESC 按键
const handleEscKey = (e) => {
  if (e.key === 'Escape' && props.visible) {
    emit('update:visible', false)
  }
}

// 组件挂载时添加键盘事件监听
onMounted(() => {
  document.addEventListener('keydown', handleEscKey)
  document.addEventListener('mousedown', closeChannelSelector)
})

// 组件卸载时移除键盘事件监听
onUnmounted(() => {
  document.removeEventListener('keydown', handleEscKey)
  document.removeEventListener('mousedown', closeChannelSelector)
})

// 拖拽相关状态
const draggedItem = ref(null)
const dragOverIndex = ref(null)

// 开始拖拽
const startDrag = (index) => {
  draggedItem.value = index
}

// 拖拽结束
const endDrag = () => {
  draggedItem.value = null
  dragOverIndex.value = null
}

// 拖拽进入目标区域
const onDragEnter = (index) => {
  if (draggedItem.value === null) return
  dragOverIndex.value = index
}

// 拖拽离开目标区域
const onDragLeave = () => {
  dragOverIndex.value = null
}

// 允许放置
const onDragOver = (e) => {
  e.preventDefault()
}

// 放置处理
const onDrop = (index) => {
  if (draggedItem.value === null) return
  
  // 获取拖拽的文件和URL
  const draggedFile = files.value[draggedItem.value]
  const draggedUrl = fileUrls.value[draggedItem.value]
  
  // 创建新的数组
  const newFiles = [...files.value]
  const newUrls = [...fileUrls.value]
  
  // 从原位置移除
  newFiles.splice(draggedItem.value, 1)
  newUrls.splice(draggedItem.value, 1)
  
  // 插入到新位置
  newFiles.splice(index, 0, draggedFile)
  newUrls.splice(index, 0, draggedUrl)
  
  // 更新数组
  files.value = newFiles
  fileUrls.value = newUrls
  
  // 重置拖拽状态
  endDrag()
}
</script>

<style scoped>
/* 优化滚动条样式 */
.overflow-auto {
  scrollbar-width: thin;
  scrollbar-color: rgba(0, 0, 0, 0.1) transparent;
}

.overflow-auto::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.overflow-auto::-webkit-scrollbar-track {
  background: transparent;
}

.overflow-auto::-webkit-scrollbar-thumb {
  background-color: rgba(0, 0, 0, 0.1);
  border-radius: 3px;
}

/* 输入框 placeholder 样式 */
input::placeholder,
textarea::placeholder {
  color: #999;
}

input:focus::placeholder,
textarea:focus::placeholder {
  color: #ccc;
}

/* 拖拽相关样式 */
[draggable] {
  user-select: none;
}

.cursor-grab {
  cursor: grab;
}

.cursor-grab:active {
  cursor: grabbing;
}
</style> 