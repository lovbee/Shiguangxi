<template>
  <div 
    class="video-player-container w-full" 
    ref="containerRef"
    @mousemove="handleMouseMove"
    @mouseleave="hideControls"
  >
    <!-- 视频元素 -->
    <video
      ref="videoRef"
      class="video-element"
      :src="videoUrl"
      :poster="poster"
      :muted="muted"
      :autoplay="autoplay"
      :loop="loop"
      :controls="showNativeControls"
      :playsinline="playsinline"
      @play="onPlay"
      @pause="onPause"
      @ended="onEnded"
      @timeupdate="onTimeUpdate"
      @loadedmetadata="onMetadataLoaded"
      @click="togglePlay"
      @error="onError"
    ></video>

    <!-- 自定义控制层 (当 useCustomControls 为 true 时显示) -->
    <div 
      v-if="useCustomControls" 
      class="custom-controls"
      :class="{ 'controls-hidden': !controlsVisible && isPlaying }"
    >
      <!-- 进度条 (单独一行) -->
      <div class="progress-container">
        <div 
          class="progress-bar" 
          @click="seekToPosition"
          @mousedown="startDragging"
        >
          <div class="progress-background"></div>
          <div class="progress-fill" :style="{ width: `${displayProgress}%` }"></div>
          <div 
            class="progress-handle" 
            :style="{ left: `${displayProgress}%` }"
            :class="{ 'handle-active': isDragging }"
          ></div>
          <div 
            v-if="showProgressTooltip || isDragging" 
            class="progress-tooltip" 
            :style="{ left: `${tooltipPosition}%` }"
          >
            {{ formatTime(previewTime) }}
          </div>
        </div>
      </div>
      
      <!-- 控制按钮和时间显示 (第二行) -->
      <div class="controls-row">
        <!-- 播放/暂停按钮 -->
        <button 
          class="play-pause-btn"
          @click.stop="togglePlay"
        >
          <svg v-if="isPlaying" class="pause-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <rect x="6" y="4" width="4" height="16" rx="1" fill="currentColor" />
            <rect x="14" y="4" width="4" height="16" rx="1" fill="currentColor" />
          </svg>
          <svg v-else class="play-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M8 5v14l11-7z" fill="currentColor" />
          </svg>
        </button>

        <!-- 时间显示 -->
        <div class="time-display">
          {{ isDragging ? formatTime(previewTime) : formatTime(currentTime) }} / {{ formatTime(duration) }}
        </div>

        <!-- 音量控制 -->
        <div class="volume-container">
          <button class="volume-btn" @click.stop="toggleMute">
            <svg v-if="isMuted" class="volume-muted-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M11 5L6 9H2v6h4l5 4V5z" fill="currentColor" />
              <path d="M23 9l-6 6M17 9l6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
            </svg>
            <svg v-else class="volume-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path d="M11 5L6 9H2v6h4l5 4V5z" fill="currentColor" />
              <path d="M15.54 8.46a5 5 0 0 1 0 7.07" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
              <path d="M19.07 4.93a10 10 0 0 1 0 14.14" stroke="currentColor" stroke-width="2" stroke-linecap="round" />
            </svg>
          </button>
          <div class="volume-slider-container">
            <input 
              type="range" 
              min="0" 
              max="1" 
              step="0.01" 
              :value="effectiveVolume"
              class="volume-slider"
              @input="updateVolume"
            />
            <div class="volume-slider-fill" :style="{ width: `${volumePercent}%` }"></div>
            <div class="volume-tooltip" :style="{ left: `${volumePercent}%` }">
              {{ Math.round(volumePercent) }}%
            </div>
          </div>
        </div>

        <!-- 全屏按钮 -->
        <button class="fullscreen-btn" @click.stop="toggleFullscreen">
          <svg v-if="isFullscreen" class="exit-fullscreen-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          <svg v-else class="fullscreen-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
      </div>
    </div>

    <!-- 大型播放按钮 (视频暂停且 useCustomControls 为 true 时显示) -->
    <div 
      v-if="useCustomControls && !isPlaying && !isEnded" 
      class="big-play-button"
      @click.stop="togglePlay"
    >
      <svg class="big-play-icon" viewBox="0 0 24 24" fill="none">
        <path d="M8 5v14l11-7z" fill="white"></path>
      </svg>
    </div>

    <!-- 重播按钮 (视频结束且 useCustomControls 为 true 时显示) -->
    <div 
      v-if="useCustomControls && isEnded" 
      class="replay-button"
      @click.stop="replay"
    >
      <svg class="replay-icon" viewBox="0 0 24 24" fill="none">
        <circle cx="12" cy="12" r="11" fill="rgba(0, 0, 0, 0.5)"/>
        <path d="M12 7C9.23858 7 7 9.23858 7 12C7 14.7614 9.23858 17 12 17C13.6569 17 15.1372 16.1652 16 14.8V16.5C16 16.7761 16.2239 17 16.5 17C16.7761 17 17 16.7761 17 16.5V13.5C17 13.2239 16.7761 13 16.5 13H13.5C13.2239 13 13 13.2239 13 13.5C13 13.7761 13.2239 14 13.5 14H15.4286C14.7412 15.1935 13.4593 16 12 16C9.79086 16 8 14.2091 8 12C8 9.79086 9.79086 8 12 8C14.2091 8 16 9.79086 16 12C16 12.2761 16.2239 12.5 16.5 12.5C16.7761 12.5 17 12.2761 17 12C17 9.23858 14.7614 7 12 7Z" fill="white"/>
      </svg>
    </div>

    <!-- 加载指示器 -->
    <div v-if="isLoading" class="loading-indicator">
      <div class="spinner"></div>
    </div>

    <!-- 错误提示 -->
    <div v-if="hasError" class="error-message">
      <svg class="error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <circle cx="12" cy="12" r="10" stroke="red" stroke-width="2" />
        <path d="M12 8v4M12 16h.01" stroke="red" stroke-width="2" stroke-linecap="round" />
      </svg>
      <span>视频加载失败</span>
      <button @click="retryLoading" class="retry-button">重试</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'

// 定义组件属性
const props = defineProps({
  // 视频URL (必需)
  videoUrl: {
    type: String,
    required: true
  },
  // 封面图URL
  poster: {
    type: String,
    default: ''
  },
  // 是否自动播放
  autoplay: {
    type: Boolean,
    default: false
  },
  // 是否循环播放
  loop: {
    type: Boolean,
    default: false
  },
  // 是否静音
  muted: {
    type: Boolean,
    default: false
  },
  // 是否使用原生控制条
  showControls: {
    type: Boolean,
    default: false
  },
  // 是否使用自定义控制条
  useCustomControls: {
    type: Boolean,
    default: true
  },
  // 是否支持行内播放 (移动端)
  playsinline: {
    type: Boolean,
    default: true
  },
  // 初始音量 (0-1)
  initialVolume: {
    type: Number,
    default: 1,
    validator: (value) => value >= 0 && value <= 1
  }
})

// 定义事件
const emit = defineEmits([
  'play',
  'pause',
  'ended',
  'timeupdate',
  'volumechange',
  'error',
  'loaded'
])

// DOM 引用
const containerRef = ref(null)
const videoRef = ref(null)

// 视频状态
const isPlaying = ref(false)
const isEnded = ref(false)
const isLoading = ref(true)
const hasError = ref(false)
const duration = ref(0)
const currentTime = ref(0)
const progress = ref(0)
const volume = ref(props.initialVolume)
const isMuted = ref(props.muted)
const isFullscreen = ref(false)

// 控制条状态
const controlsVisible = ref(true)
let controlsTimeout = null
let mouseMoveTimeout = null

// 进度条拖动状态
const isDragging = ref(false)
const showProgressTooltip = ref(false)
const tooltipPosition = ref(0)
const previewTime = ref(0)
const dragProgress = ref(0)

// 存储静音前的音量值
const lastVolume = ref(props.initialVolume)

// 计算属性
const videoElement = computed(() => videoRef.value)

// 计算属性：是否显示原生控制条
// 只有在不使用自定义控制条且showControls为true时才显示原生控制条
const showNativeControls = computed(() => {
  return props.showControls && !props.useCustomControls
})

// 计算有效音量（考虑静音状态）
const effectiveVolume = computed(() => {
  return isMuted.value ? 0 : volume.value
})

// 计算音量百分比
const volumePercent = computed(() => {
  return isMuted.value ? 0 : volume.value * 100
})

// 计算显示的进度
const displayProgress = computed(() => {
  // 如果正在拖动，显示拖动进度；否则显示实际播放进度
  return isDragging.value ? dragProgress.value : progress.value
})

// 方法
// 播放/暂停切换
const togglePlay = () => {
  if (!videoRef.value) return
  
  if (isPlaying.value) {
    videoRef.value.pause()
  } else {
    videoRef.value.play().catch(error => {
      console.error('播放失败:', error)
      hasError.value = true
    })
  }
}

// 重新播放
const replay = () => {
  if (!videoRef.value) return
  
  isEnded.value = false
  videoRef.value.currentTime = 0
  videoRef.value.play()
    .then(() => {
      isPlaying.value = true
      // 如果自动隐藏控制层，设置定时器
      if (isPlaying.value) {
        hideControlsDelayed()
      }
    })
    .catch(error => {
      console.error('播放失败:', error)
      hasError.value = true
    })
}

// 切换静音状态
const toggleMute = () => {
  if (!videoRef.value) return
  
  if (isMuted.value) {
    // 取消静音，恢复之前的音量
    isMuted.value = false
    videoRef.value.muted = false
    
    // 如果之前的音量为0，设置为默认音量
    if (lastVolume.value === 0) {
      volume.value = 0.5
      videoRef.value.volume = 0.5
    } else {
      volume.value = lastVolume.value
      videoRef.value.volume = lastVolume.value
    }
  } else {
    // 静音，保存当前音量
    lastVolume.value = volume.value
    isMuted.value = true
    videoRef.value.muted = true
  }
  
  emit('volumechange', { volume: effectiveVolume.value, muted: isMuted.value })
}

// 更新音量
const updateVolume = (e) => {
  if (!videoRef.value) return
  
  const newVolume = parseFloat(e.target.value)
  volume.value = newVolume
  videoRef.value.volume = newVolume
  
  // 如果设置的音量大于0，则取消静音状态
  if (newVolume > 0 && isMuted.value) {
    isMuted.value = false
    videoRef.value.muted = false
  }
  
  // 如果设置的音量为0，则设置为静音状态
  if (newVolume === 0 && !isMuted.value) {
    isMuted.value = true
    videoRef.value.muted = true
  }
  
  // 更新最后的非零音量
  if (newVolume > 0) {
    lastVolume.value = newVolume
  }
  
  emit('volumechange', { volume: newVolume, muted: isMuted.value })
}

// 开始拖动进度条
const startDragging = (e) => {
  if (e.button !== 0) return // 只处理左键点击
  
  isDragging.value = true
  updateDragPosition(e)
  
  // 添加全局事件监听
  document.addEventListener('mousemove', handleDragMove)
  document.addEventListener('mouseup', stopDragging)
  
  // 阻止默认行为和冒泡
  e.preventDefault()
  e.stopPropagation()
}

// 拖动过程中更新位置
const handleDragMove = (e) => {
  if (!isDragging.value) return
  updateDragPosition(e)
  
  // 实时更新视频时间位置（但不触发视频的实际播放位置变化）
  if (videoRef.value) {
    // 更新预览时间和拖动进度
    dragProgress.value = (previewTime.value / duration.value) * 100
  }
}

// 停止拖动
const stopDragging = () => {
  if (!isDragging.value) return
  
  // 应用新的播放位置
  if (videoRef.value) {
    videoRef.value.currentTime = previewTime.value
  }
  
  isDragging.value = false
  dragProgress.value = 0
  
  // 移除全局事件监听
  document.removeEventListener('mousemove', handleDragMove)
  document.removeEventListener('mouseup', stopDragging)
}

// 更新拖动位置
const updateDragPosition = (e) => {
  if (!videoRef.value || !containerRef.value) return
  
  const progressBar = containerRef.value.querySelector('.progress-bar')
  if (!progressBar) return
  
  const rect = progressBar.getBoundingClientRect()
  const offsetX = e.clientX - rect.left
  const width = rect.width
  
  // 计算百分比位置 (0-100)
  let percent = (offsetX / width) * 100
  percent = Math.max(0, Math.min(100, percent))
  
  // 更新提示位置
  tooltipPosition.value = percent
  
  // 计算预览时间
  previewTime.value = (percent / 100) * duration.value
}

// 点击进度条跳转到指定位置
const seekToPosition = (e) => {
  if (isDragging.value) return
  
  updateDragPosition(e)
  
  if (videoRef.value) {
    videoRef.value.currentTime = previewTime.value
  }
}

// 显示进度提示
const showProgressPreview = (e) => {
  showProgressTooltip.value = true
  updateDragPosition(e)
}

// 隐藏进度提示
const hideProgressPreview = () => {
  if (!isDragging.value) {
    showProgressTooltip.value = false
  }
}

// 全屏切换
const toggleFullscreen = () => {
  if (!containerRef.value) return
  
  if (!isFullscreen.value) {
    if (containerRef.value.requestFullscreen) {
      containerRef.value.requestFullscreen()
    } else if (containerRef.value.webkitRequestFullscreen) {
      containerRef.value.webkitRequestFullscreen()
    } else if (containerRef.value.msRequestFullscreen) {
      containerRef.value.msRequestFullscreen()
    }
  } else {
    if (document.exitFullscreen) {
      document.exitFullscreen()
    } else if (document.webkitExitFullscreen) {
      document.webkitExitFullscreen()
    } else if (document.msExitFullscreen) {
      document.msExitFullscreen()
    }
  }
}

// 鼠标移动处理
const handleMouseMove = () => {
  // 清除之前的定时器
  if (mouseMoveTimeout) {
    clearTimeout(mouseMoveTimeout)
  }
  
  // 显示控制层
  showControls()
  
  // 如果视频正在播放，设置定时器在一段时间后隐藏控制层
  if (isPlaying.value) {
    mouseMoveTimeout = setTimeout(() => {
      hideControls()
    }, 3000) // 3秒后隐藏
  }
}

// 显示控制层
const showControls = () => {
  controlsVisible.value = true
  
  // 清除之前的隐藏定时器
  if (controlsTimeout) {
    clearTimeout(controlsTimeout)
    controlsTimeout = null
  }
}

// 隐藏控制层
const hideControls = () => {
  // 只有在视频播放时才隐藏控制层
  if (isPlaying.value) {
    controlsVisible.value = false
  }
}

// 重试加载
const retryLoading = () => {
  if (!videoRef.value) return
  
  hasError.value = false
  isLoading.value = true
  videoRef.value.load()
}

// 格式化时间 (秒 -> MM:SS)
const formatTime = (seconds) => {
  if (isNaN(seconds) || seconds === Infinity) return '00:00'
  
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// 事件处理器
const onPlay = () => {
  isPlaying.value = true
  isEnded.value = false
  
  // 视频开始播放后，设置定时器在一段时间后隐藏控制层
  if (controlsTimeout) {
    clearTimeout(controlsTimeout)
  }
  
  controlsTimeout = setTimeout(() => {
    hideControls()
  }, 3000) // 3秒后隐藏
  
  emit('play')
}

const onPause = () => {
  isPlaying.value = false
  
  // 视频暂停时，显示控制层并清除隐藏定时器
  showControls()
  
  emit('pause')
}

const onEnded = () => {
  isPlaying.value = false
  isEnded.value = true
  controlsVisible.value = true // 确保控制层可见
  
  emit('ended')
}

const onTimeUpdate = () => {
  if (!videoRef.value || isDragging.value) return
  
  currentTime.value = videoRef.value.currentTime
  
  // 计算播放进度百分比
  if (duration.value > 0) {
    progress.value = (currentTime.value / duration.value) * 100
  }
  
  emit('timeupdate', { currentTime: currentTime.value, progress: progress.value })
}

const onMetadataLoaded = () => {
  if (!videoRef.value) return
  
  duration.value = videoRef.value.duration
  isLoading.value = false
  emit('loaded', { duration: duration.value })
}

const onError = (error) => {
  console.error('视频加载错误:', error)
  isLoading.value = false
  hasError.value = true
  emit('error', error)
}

// 监听全屏变化
const handleFullscreenChange = () => {
  isFullscreen.value = !!(
    document.fullscreenElement ||
    document.webkitFullscreenElement ||
    document.msFullscreenElement
  )
}

// 生命周期钩子
onMounted(() => {
  // 初始化视频
  if (videoRef.value) {
    // 设置初始音量
    videoRef.value.volume = volume.value
    
    // 如果自动播放，设置定时器在一段时间后隐藏控制层
    if (props.autoplay) {
      controlsTimeout = setTimeout(() => {
        hideControls()
      }, 3000)
    }
  }
  
  // 添加事件监听器
  document.addEventListener('fullscreenchange', handleFullscreenChange)
  document.addEventListener('webkitfullscreenchange', handleFullscreenChange)
  document.addEventListener('msfullscreenchange', handleFullscreenChange)
  document.addEventListener('keydown', handleKeyDown)
  
  // 为进度条添加鼠标移动事件
  const progressBar = containerRef.value?.querySelector('.progress-bar')
  if (progressBar) {
    progressBar.addEventListener('mousemove', showProgressPreview)
    progressBar.addEventListener('mouseleave', hideProgressPreview)
  }
})

onBeforeUnmount(() => {
  // 清除所有定时器
  if (controlsTimeout) {
    clearTimeout(controlsTimeout)
  }
  
  if (mouseMoveTimeout) {
    clearTimeout(mouseMoveTimeout)
  }
  
  // 移除事件监听器
  document.removeEventListener('fullscreenchange', handleFullscreenChange)
  document.removeEventListener('webkitfullscreenchange', handleFullscreenChange)
  document.removeEventListener('msfullscreenchange', handleFullscreenChange)
  document.removeEventListener('keydown', handleKeyDown)
  
  // 移除进度条事件监听
  const progressBar = containerRef.value?.querySelector('.progress-bar')
  if (progressBar) {
    progressBar.removeEventListener('mousemove', showProgressPreview)
    progressBar.removeEventListener('mouseleave', hideProgressPreview)
  }
  
  // 确保拖动事件被清理
  document.removeEventListener('mousemove', handleDragMove)
  document.removeEventListener('mouseup', stopDragging)
})

// 键盘控制
const handleKeyDown = (event) => {
  // 只有当视频播放器处于焦点状态时才响应键盘事件
  if (!containerRef.value || !containerRef.value.contains(document.activeElement)) return
  
  switch (event.key) {
    case ' ':
    case 'k':
      // 空格或K键：播放/暂停
      event.preventDefault()
      togglePlay()
      break
    case 'ArrowRight':
      // 右箭头：前进5秒
      event.preventDefault()
      if (videoRef.value) {
        videoRef.value.currentTime = Math.min(videoRef.value.currentTime + 5, duration.value)
      }
      break
    case 'ArrowLeft':
      // 左箭头：后退5秒
      event.preventDefault()
      if (videoRef.value) {
        videoRef.value.currentTime = Math.max(videoRef.value.currentTime - 5, 0)
      }
      break
    case 'm':
      // M键：静音/取消静音
      event.preventDefault()
      toggleMute()
      break
    case 'f':
      // F键：全屏/退出全屏
      event.preventDefault()
      toggleFullscreen()
      break
  }
}

// 监听属性变化
watch(() => props.muted, (newValue) => {
  if (videoRef.value) {
    videoRef.value.muted = newValue
    isMuted.value = newValue
  }
})

// 暴露方法给父组件
defineExpose({
  play: () => {
    if (videoRef.value) {
      videoRef.value.play().catch(error => {
        console.error('播放失败:', error)
        hasError.value = true
      })
    }
  },
  pause: () => {
    if (videoRef.value) {
      videoRef.value.pause()
    }
  },
  stop: () => {
    if (videoRef.value) {
      videoRef.value.pause()
      videoRef.value.currentTime = 0
    }
  },
  seek: (time) => {
    if (videoRef.value) {
      videoRef.value.currentTime = time
    }
  },
  setVolume: (value) => {
    if (videoRef.value && value >= 0 && value <= 1) {
      volume.value = value
      videoRef.value.volume = value
    }
  },
  mute: () => {
    if (videoRef.value) {
      isMuted.value = true
      videoRef.value.muted = true
    }
  },
  unmute: () => {
    if (videoRef.value) {
      isMuted.value = false
      videoRef.value.muted = false
    }
  },
  toggleFullscreen,
  videoElement
})
</script>

<style scoped>
/* 视频播放器容器 */
.video-player-container {
  position: relative;
  width: 100%;
  min-width: 480px;
  max-width: 800px;
  height: 100%;
  background-color: #000;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
}



.video-element {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background-color: #000;
}

/* 自定义控制条 */
.custom-controls {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(transparent, rgba(0, 0, 0, 0.7));
  padding: 0;
  display: flex;
  flex-direction: column;
  transition: opacity 0.3s ease;
  z-index: 2;
}

.controls-hidden {
  opacity: 0;
  pointer-events: none;
}

/* 控制按钮行 */
.controls-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
}

/* 进度条容器 */
.progress-container {
  width: 100%;
  padding: 10px 10px 0 10px;
}

.progress-bar {
  height: 4px;
  position: relative;
  cursor: pointer;
  overflow: visible;
  transition: height 0.2s;
  border-radius: 2px;
}

.progress-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
}

.progress-fill {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background-color: white;
  border-radius: 2px;
  pointer-events: none;
  z-index: 2;
}

.progress-bar:hover {
  height: 6px;
}

.progress-bar:hover .progress-background,
.progress-bar:hover .progress-fill {
  height: 100%;
}

/* 时间显示 */
.time-display {
  font-size: 12px;
  color: white;
  margin-right: auto; /* 将时间显示推到左侧，紧跟播放按钮 */
}

.play-pause-btn,
.volume-btn,
.fullscreen-btn {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background-color 0.2s;
}

.play-pause-btn:hover,
.volume-btn:hover,
.fullscreen-btn:hover {
  background-color: rgba(255, 255, 255, 0.2);
}

.play-icon,
.pause-icon,
.volume-icon,
.volume-muted-icon,
.fullscreen-icon,
.exit-fullscreen-icon {
  width: 20px;
  height: 20px;
}

/* 音量控制容器 */
.volume-container {
  display: flex;
  align-items: center;
  gap: 5px;
  position: relative;
}

/* 音量滑块容器 */
.volume-slider-container {
  width: 60px;
  height: 4px;
  position: relative;
  display: flex;
  align-items: center;
}

/* 音量滑块 */
.volume-slider {
  width: 100%;
  height: 100%;
  -webkit-appearance: none;
  background-color: transparent;
  border-radius: 2px;
  outline: none;
  position: absolute;
  top: 0;
  left: 0;
  margin: 0;
  z-index: 3;
  cursor: pointer;
}

/* 音量滑块背景 */
.volume-slider-container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
  z-index: 1;
}

/* 音量滑块填充 */
.volume-slider-fill {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  background-color: white;
  border-radius: 2px;
  pointer-events: none;
  z-index: 2;
  transition: width 0.1s ease;
}

/* 音量滑块拇指 */
.volume-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: white;
  cursor: pointer;
  position: relative;
  z-index: 4;
}

.volume-slider::-moz-range-thumb {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: white;
  cursor: pointer;
  border: none;
  position: relative;
  z-index: 4;
}

/* 音量提示框 */
.volume-tooltip {
  position: absolute;
  top: -25px;
  transform: translateX(-50%);
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  opacity: 0;
  transition: opacity 0.2s;
  pointer-events: none;
  white-space: nowrap;
  z-index: 5;
}

/* 鼠标悬停时显示提示框 */
.volume-slider-container:hover .volume-tooltip {
  opacity: 1;
}

/* 全屏样式 */
:fullscreen .video-player-container {
  width: 100vw;
  height: 100vh;
}

:-webkit-full-screen .video-player-container {
  width: 100vw;
  height: 100vh;
}

:-ms-fullscreen .video-player-container {
  width: 100vw;
  height: 100vh;
}

/* 进度条拖动手柄 */
.progress-handle {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: white;
  opacity: 0;
  transition: opacity 0.2s;
  pointer-events: none;
  z-index: 3;
}

.progress-bar:hover .progress-handle {
  opacity: 1;
}

.handle-active {
  opacity: 1 !important;
  transform: translate(-50%, -50%) scale(1.2);
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.3);
}

/* 进度条提示框 */
.progress-tooltip {
  position: absolute;
  top: -30px;
  transform: translateX(-50%);
  background-color: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
  pointer-events: none;
  white-space: nowrap;
  z-index: 4;
}

/* 大型播放按钮 */
.big-play-button {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  cursor: pointer;
  z-index: 2;
  transition: transform 0.2s;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
}

.big-play-button:hover {
  transform: translate(-50%, -50%) scale(1.1);
  background-color: rgba(0, 0, 0, 0.7);
}

.big-play-icon {
  width: 32px;
  height: 32px;
}

/* 重播按钮 */
.replay-button {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  cursor: pointer;
  z-index: 2;
  transition: transform 0.2s;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background-color: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
}

.replay-button:hover {
  transform: translate(-50%, -50%) scale(1.1);
  background-color: rgba(0, 0, 0, 0.5);
}

.replay-icon {
  width: 64px;
  height: 64px;
}
</style> 