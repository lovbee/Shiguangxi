<template>
  <div class="tab-nav">
    <div class="tab-list">
      <button 
        v-for="tab in tabs" 
        :key="tab.key"
        class="tab-item"
        :class="{ 'active': modelValue === tab.key }"
        @click="$emit('update:modelValue', tab.key)"
      >
        <span class="tab-text text-[16px]">{{ tab.label }}</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  tabs: {
    type: Array,
    required: true
  },
  modelValue: {
    type: String,
    required: true
  }
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.tab-nav {
  width: 100%;
}

.tab-list {
  display: flex;
  gap: 5px;
  justify-content: center;
}

.tab-item {
  position: relative;
  width: 64px;
  height: 44px;
  padding: 0;
  font-size: 14px;
  color: var(--color-secondary-label);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  border: none;
  background: none;
  cursor: pointer;
}

.tab-item.active {
    color: var(--color-primary-label);
  font-weight: 600;
  /* padding: 0px 16px; */
  background-color: #f5f5f5;
  border-radius: 20px;
}

.tab-item:hover {
    color: var(--color-primary-label);
}


.tab-count {
  color: #999;
  font-size: 14px;
}

.tab-item.active .tab-count {
  color: #333;
}
</style> 