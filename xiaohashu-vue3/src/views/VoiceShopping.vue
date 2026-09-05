<template>
  <div class="voice-shopping-page">
    <header class="voice-page-header">
      <div>
        <p class="voice-page-kicker">AI SHOPPING ASSISTANT</p>
        <h1>智能导购</h1>
        <p>说出需求，获取商品推荐与语音答复。</p>
      </div>
      <button
        class="voice-icon-button"
        type="button"
        title="新建导购会话"
        aria-label="新建导购会话"
        :disabled="!isLoggedIn || isInitializing || isRecording || isProcessing"
        @click="resetSession"
      >
        <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path d="M20 11a8 8 0 1 1-2.35-5.65M20 4v7h-7" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </button>
    </header>

    <section v-if="!isLoggedIn" class="voice-login-state" aria-live="polite">
      <div>
        <h2>登录后开始智能导购</h2>
        <p>语音会话会使用当前小哈书账号的登录状态。</p>
      </div>
      <button type="button" class="voice-command-button" @click="requestLogin">登录</button>
    </section>

    <div v-else class="voice-workspace">
      <section class="voice-control-surface" aria-labelledby="voice-control-title">
        <div class="surface-heading">
          <div>
            <p class="section-label">VOICE INPUT</p>
            <h2 id="voice-control-title">{{ controlTitle }}</h2>
          </div>
          <span class="connection-state" :class="connectionTone">
            <i></i>{{ connectionLabel }}
          </span>
        </div>

        <div class="voice-stage">
          <button
            class="voice-mic-button"
            :class="{ recording: isRecording, processing: isProcessing }"
            type="button"
            :title="micButtonLabel"
            :aria-label="micButtonLabel"
            :disabled="isInitializing || isTextSending || isProcessing"
            @click="handleMicClick"
          >
            <svg v-if="!isRecording" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <rect x="8" y="3" width="8" height="12" rx="4" stroke="currentColor" stroke-width="1.8" />
              <path d="M5 11a7 7 0 0 0 14 0M12 18v3M8.5 21h7" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" />
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <rect x="7" y="7" width="10" height="10" rx="1.5" fill="currentColor" />
            </svg>
          </button>
          <p class="voice-stage-title">{{ micButtonLabel }}</p>
          <p class="voice-stage-hint">{{ stageHint }}</p>
          <div class="voice-meter" :class="{ active: isRecording }" aria-hidden="true">
            <span v-for="bar in 11" :key="bar"></span>
          </div>
        </div>

        <p v-if="serviceError" class="voice-notice error" role="alert">{{ serviceError }}</p>
        <p v-else-if="serviceWarning" class="voice-notice warning">{{ serviceWarning }}</p>

        <form class="text-entry" @submit.prevent="sendText">
          <label for="voice-text-input">文字输入</label>
          <div class="text-entry-row">
            <input
              id="voice-text-input"
              v-model="textInput"
              type="text"
              maxlength="500"
              placeholder="例如：通勤用的轻便双肩包，预算 500 元以内"
              :disabled="isInitializing || isTextSending || isRecording || isProcessing"
            />
            <button
              type="submit"
              class="voice-icon-button send"
              title="发送文字需求"
              aria-label="发送文字需求"
              :disabled="!textInput.trim() || isInitializing || isTextSending || isRecording || isProcessing"
            >
              <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
                <path d="m4 4 16 8-16 8 3-8-3-8Z" stroke="currentColor" stroke-width="1.9" stroke-linejoin="round" />
              </svg>
            </button>
          </div>
        </form>

        <footer class="voice-session-meta">
          <span>会话</span>
          <code>{{ sessionId || '准备中' }}</code>
        </footer>
      </section>

      <section class="voice-result-surface" aria-labelledby="voice-result-title">
        <div class="surface-heading result-heading">
          <div>
            <p class="section-label">LIVE RESULT</p>
            <h2 id="voice-result-title">本轮结果</h2>
          </div>
          <span class="result-count">{{ recommendations.length }} 款推荐</span>
        </div>

        <div class="transcript-block">
          <span>识别内容</span>
          <p>{{ transcript || '开始录音后，这里会显示实时识别内容。' }}</p>
        </div>

        <div class="assistant-reply">
          <span>导购答复</span>
          <p>{{ assistantReply || '等待你的需求。' }}</p>
        </div>

        <div class="recommendation-section">
          <div class="recommendation-title-row">
            <h3>推荐商品</h3>
            <span v-if="audioReceived" class="audio-state"><i></i>语音回复已接收</span>
          </div>
          <div v-if="recommendations.length" class="recommendation-list">
            <article v-for="(item, index) in recommendations" :key="item.productId || `${item.name}-${index}`" class="recommendation-item">
              <span class="product-rank">{{ String(index + 1).padStart(2, '0') }}</span>
              <div class="product-detail">
                <h4>{{ item.name || '未命名商品' }}</h4>
                <p>{{ item.reason || '已根据本轮需求加入推荐。' }}</p>
              </div>
              <strong>{{ formatPrice(item.price) }}</strong>
            </article>
          </div>
          <div v-else class="recommendation-empty">
            <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path d="M6 8.5V7a6 6 0 0 1 12 0v1.5M5 8.5h14l-1 11H6l-1-11Z" stroke="currentColor" stroke-width="1.7" stroke-linejoin="round" />
            </svg>
            <p>推荐商品将在本轮答复中出现。</p>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, inject, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { startVoiceSession, sendVoiceShoppingText } from '@/api/voiceAgent'
import { useVoiceAgentSocket } from '@/composables/useVoiceAgentSocket'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const showLoginModal = inject('showLoginModal')

const sessionId = ref('')
const sessionReady = ref(false)
const isInitializing = ref(false)
const isTextSending = ref(false)
const transcript = ref('')
const assistantReply = ref('')
const recommendations = ref([])
const serviceError = ref('')
const serviceWarning = ref('')
const audioReceived = ref(false)
const textInput = ref('')

const isLoggedIn = computed(() => Boolean(userStore.token))

const {
  status,
  isRecording,
  isProcessing,
  beginRecording,
  stopRecording,
  dispose,
} = useVoiceAgentSocket({
  onEvent: handleSocketEvent,
  onError: (message) => {
    serviceError.value = message
  },
})

const connectionLabel = computed(() => {
  if (isInitializing.value) return '正在创建会话'
  if (isRecording.value) return '正在录音'
  if (isProcessing.value) return '正在生成答复'
  if (status.value === 'error' || serviceError.value) return '连接异常'
  return sessionReady.value ? '服务可用' : '等待开始'
})

const connectionTone = computed(() => {
  if (isInitializing.value || isProcessing.value) return 'busy'
  if (isRecording.value || sessionReady.value) return 'online'
  if (status.value === 'error' || serviceError.value) return 'error'
  return ''
})

const controlTitle = computed(() => {
  if (isInitializing.value) return '正在准备会话'
  if (isRecording.value) return '正在聆听'
  if (isProcessing.value) return '正在整理推荐'
  return sessionReady.value ? '描述你的购物需求' : '等待会话就绪'
})

const micButtonLabel = computed(() => {
  if (isRecording.value) return '结束录音'
  if (isProcessing.value) return '正在生成答复'
  if (isInitializing.value) return '正在准备'
  return '开始语音输入'
})

const stageHint = computed(() => {
  if (isRecording.value) return '说完后再次点击按钮提交本轮语音。'
  if (isProcessing.value) return '正在识别语音、匹配商品并生成答复。'
  if (sessionReady.value) return '点击麦克风开始一轮语音导购。'
  return '会话准备完成后即可开始。'
})

function createSessionId() {
  if (window.crypto?.randomUUID) return `voice-${window.crypto.randomUUID()}`
  return `voice-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function clearRoundResult() {
  transcript.value = ''
  assistantReply.value = ''
  recommendations.value = []
  serviceError.value = ''
  serviceWarning.value = ''
  audioReceived.value = false
}

async function ensureSession() {
  if (!isLoggedIn.value) return false
  if (sessionReady.value) return true
  if (isInitializing.value) return false

  isInitializing.value = true
  serviceError.value = ''
  try {
    sessionId.value = createSessionId()
    await startVoiceSession({ sessionId: sessionId.value, channel: 'HOME_ENTRY' })
    sessionReady.value = true
    return true
  } catch (error) {
    sessionReady.value = false
    serviceError.value = error?.message || '无法创建导购会话，请稍后重试。'
    return false
  } finally {
    isInitializing.value = false
  }
}

async function handleMicClick() {
  if (!isLoggedIn.value) {
    requestLogin()
    return
  }
  if (isRecording.value) {
    stopRecording()
    return
  }
  if (isProcessing.value) return
  if (!(await ensureSession())) return
  clearRoundResult()
  await beginRecording(sessionId.value)
}

function handleSocketEvent(message) {
  switch (message.type) {
    case 'asr':
      transcript.value = message.text || '（未识别到内容）'
      break
    case 'recommendation':
      recommendations.value = Array.isArray(message.items) ? message.items : []
      break
    case 'caption':
      assistantReply.value += message.text || ''
      break
    case 'warning':
      serviceWarning.value = message.message || '文字答复已生成，语音合成暂不可用。'
      break
    case 'complete':
      if (message.audioAvailable === false) {
        serviceWarning.value = '文字答复已生成，语音合成暂不可用。'
      }
      break
    case 'error':
      serviceError.value = message.message || '本轮语音导购失败，请重试。'
      break
    case 'audio':
      audioReceived.value = true
      break
    default:
      break
  }
}

async function sendText() {
  const utterance = textInput.value.trim()
  if (!utterance || isTextSending.value) return
  if (!(await ensureSession())) return

  isTextSending.value = true
  clearRoundResult()
  transcript.value = utterance
  try {
    const result = await sendVoiceShoppingText({ sessionId: sessionId.value, utterance })
    assistantReply.value = result?.speechText || ''
    recommendations.value = Array.isArray(result?.displayBlocks) ? result.displayBlocks : []
    textInput.value = ''
  } catch (error) {
    serviceError.value = error?.message || '文字导购请求失败，请稍后重试。'
  } finally {
    isTextSending.value = false
  }
}

async function resetSession() {
  await dispose()
  sessionReady.value = false
  clearRoundResult()
  await ensureSession()
}

function requestLogin() {
  if (showLoginModal) showLoginModal.value = true
}

function formatPrice(price) {
  if (price === undefined || price === null || price === '') return '价格待确认'
  const value = Number(price)
  return Number.isFinite(value) ? `¥${value.toFixed(2)}` : `¥${price}`
}

watch(isLoggedIn, async (loggedIn) => {
  if (loggedIn) {
    await ensureSession()
  } else {
    await dispose()
    sessionReady.value = false
    sessionId.value = ''
    clearRoundResult()
  }
})

onMounted(() => {
  if (isLoggedIn.value) ensureSession()
})

onBeforeUnmount(() => {
  dispose()
})
</script>

<style scoped>
.voice-shopping-page {
  min-height: calc(100vh - 148px);
  padding: 6px 0 48px;
  color: #1f2937;
}

.voice-page-header,
.surface-heading,
.recommendation-title-row,
.text-entry-row,
.voice-login-state {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.voice-page-header {
  margin: 4px 0 22px;
}

.voice-page-kicker,
.section-label {
  margin: 0 0 5px;
  color: #8a97a8;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0;
}

.voice-page-header h1,
.surface-heading h2,
.voice-login-state h2 {
  margin: 0;
  color: #25282d;
  font-size: 22px;
  line-height: 1.3;
  font-weight: 700;
}

.voice-page-header p:not(.voice-page-kicker),
.voice-login-state p {
  margin: 6px 0 0;
  color: #748092;
  font-size: 13px;
  line-height: 1.6;
}

.voice-icon-button {
  display: inline-grid;
  width: 38px;
  height: 38px;
  place-items: center;
  flex: 0 0 auto;
  color: #536071;
  background: #fff;
  border: 1px solid #e3e6eb;
  border-radius: 8px;
  cursor: pointer;
  transition: background .16s ease, color .16s ease, border-color .16s ease;
}

.voice-icon-button:hover:not(:disabled) {
  color: #20242a;
  background: #f7f8fa;
  border-color: #cad0d9;
}

.voice-icon-button:disabled,
.voice-command-button:disabled,
.voice-mic-button:disabled {
  cursor: not-allowed;
  opacity: .48;
}

.voice-icon-button svg { width: 18px; height: 18px; }

.voice-login-state {
  padding: 22px 24px;
  background: #fff;
  border: 1px solid #e6e9ee;
  border-radius: 8px;
}

.voice-login-state h2 { font-size: 17px; }

.voice-command-button {
  min-height: 36px;
  padding: 0 17px;
  color: #fff;
  background: #ff2442;
  border: 1px solid #ff2442;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
}

.voice-workspace {
  display: grid;
  grid-template-columns: minmax(330px, .84fr) minmax(430px, 1.16fr);
  gap: 18px;
  align-items: start;
}

.voice-control-surface,
.voice-result-surface {
  min-width: 0;
  background: #fff;
  border: 1px solid #e6e9ee;
  border-radius: 8px;
}

.voice-control-surface { overflow: hidden; }

.surface-heading { padding: 20px 22px 0; }
.surface-heading h2 { font-size: 17px; }

.connection-state,
.result-count,
.audio-state {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: #7a8797;
  font-size: 12px;
  white-space: nowrap;
}

.connection-state i,
.audio-state i {
  width: 7px;
  height: 7px;
  background: #a3acb8;
  border-radius: 50%;
}

.connection-state.online { color: #14755c; }
.connection-state.online i,
.audio-state i { background: #21a678; }
.connection-state.busy { color: #a7660c; }
.connection-state.busy i { background: #e7a125; }
.connection-state.error { color: #c43d45; }
.connection-state.error i { background: #d94a53; }

.voice-stage {
  display: grid;
  justify-items: center;
  min-height: 330px;
  padding: 37px 24px 26px;
  color: #f6f8fb;
  text-align: center;
  background: #202a35;
}

.voice-mic-button {
  display: grid;
  width: 110px;
  height: 110px;
  place-items: center;
  color: #fff;
  background: #ff3651;
  border: 8px solid rgba(255,255,255,.12);
  border-radius: 50%;
  box-shadow: 0 0 0 1px rgba(255,255,255,.08), 0 12px 28px rgba(0,0,0,.22);
  cursor: pointer;
  transition: transform .16s ease, background .16s ease;
}

.voice-mic-button:hover:not(:disabled) { transform: translateY(-2px); background: #f51f3e; }
.voice-mic-button.recording { background: #d73d49; animation: voice-pulse 1.5s ease-in-out infinite; }
.voice-mic-button.processing { background: #b98222; }
.voice-mic-button svg { width: 34px; height: 34px; }

.voice-stage-title { margin: 17px 0 0; font-size: 15px; font-weight: 700; }
.voice-stage-hint { max-width: 270px; margin: 7px 0 0; color: #abb6c4; font-size: 12px; line-height: 1.55; }

.voice-meter {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  height: 26px;
  margin-top: 17px;
}

.voice-meter span { width: 4px; height: 7px; background: #526172; border-radius: 4px; }
.voice-meter.active span { background: #f2a2ad; animation: meter-wave .9s ease-in-out infinite alternate; }
.voice-meter.active span:nth-child(2n) { animation-delay: -.2s; }
.voice-meter.active span:nth-child(3n) { animation-delay: -.45s; }

.voice-notice { margin: 14px 20px 0; padding: 10px 12px; border-radius: 6px; font-size: 12px; line-height: 1.5; }
.voice-notice.error { color: #b93740; background: #fff3f4; border: 1px solid #ffd7da; }
.voice-notice.warning { color: #985e0d; background: #fff9ed; border: 1px solid #f6dfad; }

.text-entry { padding: 18px 20px 14px; }
.text-entry label { display: block; margin-bottom: 8px; color: #697687; font-size: 12px; font-weight: 700; }
.text-entry-row { gap: 8px; }
.text-entry input {
  width: 100%;
  height: 40px;
  min-width: 0;
  padding: 0 12px;
  color: #2a3038;
  background: #f8f9fb;
  border: 1px solid #e2e6ec;
  border-radius: 7px;
  outline: none;
  font-size: 13px;
}
.text-entry input:focus { background: #fff; border-color: #ff9cab; box-shadow: 0 0 0 3px rgba(255,36,66,.1); }
.voice-icon-button.send { color: #fff; background: #ff2442; border-color: #ff2442; }
.voice-icon-button.send:hover:not(:disabled) { background: #ec1635; border-color: #ec1635; }

.voice-session-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 44px;
  padding: 0 20px;
  color: #8a97a8;
  background: #fafbfc;
  border-top: 1px solid #edf0f3;
  font-size: 11px;
}
.voice-session-meta code { overflow: hidden; color: #697687; text-overflow: ellipsis; white-space: nowrap; }

.voice-result-surface { padding-bottom: 8px; }
.result-heading { padding-bottom: 18px; border-bottom: 1px solid #edf0f3; }
.result-count { color: #7b8795; }

.transcript-block,
.assistant-reply { padding: 16px 22px; border-bottom: 1px solid #edf0f3; }
.transcript-block span,
.assistant-reply span { display: block; margin-bottom: 7px; color: #8b96a5; font-size: 11px; font-weight: 700; }
.transcript-block p,
.assistant-reply p { margin: 0; color: #35404d; font-size: 14px; line-height: 1.7; white-space: pre-wrap; }
.transcript-block { background: #fcfcfd; }

.recommendation-section { padding: 18px 22px 14px; }
.recommendation-title-row { margin-bottom: 12px; }
.recommendation-title-row h3 { margin: 0; color: #29323d; font-size: 14px; }
.audio-state { color: #14755c; }

.recommendation-list { border-top: 1px solid #edf0f3; }
.recommendation-item {
  display: grid;
  grid-template-columns: 30px minmax(0, 1fr) auto;
  gap: 11px;
  align-items: center;
  min-height: 72px;
  border-bottom: 1px solid #edf0f3;
}
.product-rank { color: #96a1ae; font-size: 12px; font-variant-numeric: tabular-nums; }
.product-detail { min-width: 0; }
.product-detail h4 { overflow: hidden; margin: 0; color: #2d3540; font-size: 13px; text-overflow: ellipsis; white-space: nowrap; }
.product-detail p { display: -webkit-box; overflow: hidden; margin: 5px 0 0; color: #7a8796; font-size: 12px; line-height: 1.45; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }
.recommendation-item strong { color: #e83c4e; font-size: 13px; white-space: nowrap; }

.recommendation-empty { display: grid; min-height: 180px; place-items: center; align-content: center; color: #a0aab7; text-align: center; }
.recommendation-empty svg { width: 28px; height: 28px; }
.recommendation-empty p { margin: 9px 0 0; font-size: 12px; }

@keyframes voice-pulse {
  0%, 100% { box-shadow: 0 0 0 1px rgba(255,255,255,.08), 0 0 0 0 rgba(215,61,73,.38); }
  55% { box-shadow: 0 0 0 1px rgba(255,255,255,.08), 0 0 0 13px rgba(215,61,73,0); }
}

@keyframes meter-wave { from { height: 7px; } to { height: 23px; } }

@media (max-width: 1120px) {
  .voice-workspace { grid-template-columns: 1fr; }
}

@media (max-width: 640px) {
  .voice-page-header { align-items: flex-start; }
  .voice-login-state { align-items: flex-start; flex-direction: column; }
  .surface-heading { align-items: flex-start; }
  .voice-stage { min-height: 300px; }
  .voice-session-meta code { max-width: 220px; }
}
</style>
