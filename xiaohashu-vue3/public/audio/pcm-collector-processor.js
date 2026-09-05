class PcmCollector extends AudioWorkletProcessor {
  constructor(options) {
    super()
    this.inputRate = options.processorOptions.inputRate
    this.targetRate = 16000
    this.ratio = this.inputRate / this.targetRate
    this.samplesPerChunk = this.targetRate / 10
    this.buffer = new Int16Array(this.samplesPerChunk)
    this.cursor = 0
    this.sourceIndex = 0
  }

  process(inputs) {
    const input = inputs[0]?.[0]
    if (!input) return true
    while (this.sourceIndex < input.length) {
      const first = Math.floor(this.sourceIndex)
      const fraction = this.sourceIndex - first
      const start = input[first] || 0
      const end = input[first + 1] || start
      const sample = Math.max(-1, Math.min(1, start + (end - start) * fraction))
      this.buffer[this.cursor++] = sample < 0 ? sample * 0x8000 : sample * 0x7fff
      if (this.cursor === this.buffer.length) {
        this.port.postMessage({ type: 'pcm', data: this.buffer.buffer.slice(0) })
        this.cursor = 0
      }
      this.sourceIndex += this.ratio
    }
    this.sourceIndex -= input.length
    return true
  }
}

registerProcessor('pcm-collector', PcmCollector)
