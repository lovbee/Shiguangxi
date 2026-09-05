import axios from '@/axios'

const API_PREFIX = '/agent'

function unwrap(response) {
  if (!response?.success) {
    throw new Error(response?.message || '智能导购服务暂不可用')
  }
  return response.data
}

export async function startVoiceSession(payload) {
  return unwrap(await axios.post(`${API_PREFIX}/sessions`, payload))
}

export async function sendVoiceShoppingText(payload) {
  return unwrap(await axios.post(`${API_PREFIX}/chat/text`, payload))
}

export async function getVoiceAgentOrders() {
  return unwrap(await axios.get(`${API_PREFIX}/orders/mine`))
}
