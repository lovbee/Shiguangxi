import { computed, ref } from 'vue'

const TARGET_SAMPLE_RATE = 16000
const SILENCE_TAIL_MS = 800
const CONNECT_TIMEOUT_MS = 10000
const WORKLET_URL = `${import.meta.env.BASE_URL}audio/pcm-collector-processor.js`

function buildSocketUrl(sessionId) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  // 浏览器会自动携带同源 HttpOnly Cookie；不能把登录 token 放入 URL。
  const url = new URL(`${protocol}//${window.location.host}/api/agent/ws/voice`)
  url.searchParams.set('sessionId', sessionId)
  return url.toString()
}

export function useVoiceAgentSocket({ onEvent, onError } = {}) {
  const status = ref('idle')
  const isRecording = ref(false)
  const isProcessing = ref(false)
  const isConnected = computed(() => ['ready', 'recording', 'processing'].includes(status.value))

  let socket = null
  let audioContext = null
  let inputStream = null
  let inputSource = null
  let workletNode = null
  let workletLoaded = false
  let playbackTime = 0
  let completed = false
  let closing = false

  function emitError(message) {
    onError?.(message)
  }

  function connectionFailureMessage(event) {
    if (event?.code === 1008) {
      return '登录状态已失效，请重新登录后再使用语音导购。'
    }
    return '语音通道连接失败，请确认登录状态后重试。'
  }

  function waitForSocketOpen(activeSocket) {
    return new Promise((resolve, reject) => {
      let settled = false
      let timeoutId = null

      const cleanup = () => {
        if (timeoutId !== null) window.clearTimeout(timeoutId)
        activeSocket.removeEventListener('open', handleOpen)
        activeSocket.removeEventListener('error', handleError)
        activeSocket.removeEventListener('close', handleClose)
      }

      const settle = (callback, value) => {
        if (settled) return
        settled = true
        cleanup()
        callback(value)
      }

      const handleOpen = () => settle(resolve)
      const handleError = () => settle(reject, new Error(connectionFailureMessage()))
      const handleClose = (event) => settle(reject, new Error(connectionFailureMessage(event)))

      timeoutId = window.setTimeout(() => {
        if (activeSocket.readyState === WebSocket.CONNECTING) {
          try { activeSocket.close() } catch (_) {}
        }
        settle(reject, new Error('语音通道连接超时，请稍后重试。'))
      }, CONNECT_TIMEOUT_MS)

      activeSocket.addEventListener('open', handleOpen)
      activeSocket.addEventListener('error', handleError)
      activeSocket.addEventListener('close', handleClose)
    })
  }

  function releaseInput() {
    if (inputSource) {
      try { inputSource.disconnect() } catch (_) {}
      inputSource = null
    }
    if (workletNode) {
      workletNode.port.onmessage = null
      try { workletNode.disconnect() } catch (_) {}
      workletNode = null
    }
    if (inputStream) {
      inputStream.getTracks().forEach((track) => track.stop())
      inputStream = null
    }
  }

  async function ensureAudioContext() {
    if (!audioContext || audioContext.state === 'closed') {
      audioContext = new AudioContext()
      workletLoaded = false
      playbackTime = 0
    }
    if (!workletLoaded) {
      await audioContext.audioWorklet.addModule(WORKLET_URL)
      workletLoaded = true
    }
    await audioContext.resume()
  }

  function queuePcmPlayback(arrayBuffer) {
    if (!audioContext || audioContext.state === 'closed') return
    const view = new DataView(arrayBuffer)
    const samples = new Float32Array(view.byteLength / 2)
    for (let index = 0; index < samples.length; index += 1) {
      const value = view.getInt16(index * 2, true)
      samples[index] = value < 0 ? value / 0x8000 : value / 0x7fff
    }
    const buffer = audioContext.createBuffer(1, samples.length, TARGET_SAMPLE_RATE)
    buffer.getChannelData(0).set(samples)
    const source = audioContext.createBufferSource()
    source.buffer = buffer
    source.connect(audioContext.destination)
    const startAt = Math.max(audioContext.currentTime, playbackTime)
    source.start(startAt)
    playbackTime = startAt + buffer.duration
  }

  function closeSocket() {
    const activeSocket = socket
    socket = null
    if (activeSocket && (activeSocket.readyState === WebSocket.OPEN || activeSocket.readyState === WebSocket.CONNECTING)) {
      try { activeSocket.close() } catch (_) {}
    }
  }

  async function beginRecording(sessionId) {
    if (isRecording.value || isProcessing.value) return

    completed = false
    closing = false
    status.value = 'connecting'
    playbackTime = 0

    try {
      closeSocket()
      const activeSocket = new WebSocket(buildSocketUrl(sessionId))
      socket = activeSocket
      activeSocket.binaryType = 'arraybuffer'
      await waitForSocketOpen(activeSocket)

      if (socket !== activeSocket) {
        return
      }

      activeSocket.onmessage = (event) => {
        if (typeof event.data !== 'string') {
          queuePcmPlayback(event.data)
          onEvent?.({ type: 'audio' })
          return
        }
        try {
          const message = JSON.parse(event.data)
          if (message.type === 'complete') {
            completed = true
            isProcessing.value = false
            status.value = 'ready'
          }
          if (message.type === 'error') {
            completed = true
            isProcessing.value = false
            status.value = 'error'
          }
          onEvent?.(message)
        } catch (_) {
          emitError('智能导购返回了无法识别的消息。')
        }
      }

      activeSocket.onclose = () => {
        if (socket !== activeSocket) return
        socket = null
        const shouldReportFailure = !closing && !completed && (isRecording.value || isProcessing.value)
        isRecording.value = false
        isProcessing.value = false
        if (shouldReportFailure) {
          status.value = 'error'
          emitError('语音通道已断开，本轮对话没有完成。')
        } else if (status.value !== 'error') {
          status.value = 'idle'
        }
      }

      activeSocket.onerror = () => {
        if (!completed) emitError('语音通道出现网络异常。')
      }

      await ensureAudioContext()
      if (!navigator.mediaDevices?.getUserMedia) {
        throw new Error('当前浏览器不支持麦克风采集，请使用最新版浏览器。')
      }
      inputStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          echoCancellation: true,
          autoGainControl: true,
          noiseSuppression: true,
        },
      })
      inputSource = audioContext.createMediaStreamSource(inputStream)
      workletNode = new AudioWorkletNode(audioContext, 'pcm-collector', {
        processorOptions: { inputRate: audioContext.sampleRate },
      })
      workletNode.port.onmessage = (event) => {
        if (isRecording.value && event.data.type === 'pcm' && activeSocket.readyState === WebSocket.OPEN && socket === activeSocket) {
          activeSocket.send(event.data.data)
        }
      }
      inputSource.connect(workletNode)
      isRecording.value = true
      status.value = 'recording'
    } catch (error) {
      isRecording.value = false
      isProcessing.value = false
      status.value = 'error'
      releaseInput()
      closeSocket()
      emitError(error?.message || '无法启动录音，请检查麦克风权限。')
    }
  }

  function stopRecording() {
    if (!isRecording.value || isProcessing.value) return
    isRecording.value = false
    isProcessing.value = true
    status.value = 'processing'
    releaseInput()
    const activeSocket = socket
    if (activeSocket?.readyState === WebSocket.OPEN) {
      try {
        activeSocket.send(new Int16Array((TARGET_SAMPLE_RATE * SILENCE_TAIL_MS) / 1000).buffer)
        activeSocket.send(JSON.stringify({ type: 'audio_end' }))
      } catch (_) {
        isProcessing.value = false
        status.value = 'error'
        emitError('语音通道已断开，无法提交本轮录音。')
      }
    } else {
      isProcessing.value = false
      status.value = 'error'
      emitError('语音通道未连接，无法提交本轮录音。')
    }
  }

  async function dispose() {
    closing = true
    isRecording.value = false
    isProcessing.value = false
    releaseInput()
    closeSocket()
    if (audioContext && audioContext.state !== 'closed') {
      await audioContext.close().catch(() => {})
    }
    audioContext = null
    workletLoaded = false
    status.value = 'idle'
  }

  return { status, isRecording, isProcessing, isConnected, beginRecording, stopRecording, dispose }
}
