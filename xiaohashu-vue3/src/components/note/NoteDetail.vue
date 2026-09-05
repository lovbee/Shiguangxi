<template>
  <div class="note-detail">
    <!-- 其他内容 -->
    <div class="note-channel">
      频道: {{ channelStore.getChannelNameById(note.channelId) }}
    </div>
    <!-- 其他内容 -->
  </div>
</template>

<script setup>
import { useChannelStore } from '@/stores/channel'

const channelStore = useChannelStore()
const props = defineProps({
  note: Object
})
</script> 