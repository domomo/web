<script setup>
defineProps({
  as: { type: String, default: 'div' },
  tone: { type: String, default: 'default', validator: (value) => ['default', 'soft'].includes(value) },
});
</script>

<template>
  <component :is="as" class="surface-panel" :class="`surface-panel--${tone}`"><slot /></component>
</template>

<style scoped>
.surface-panel { border: 1px solid #e5e8eb; border-radius: 18px; background: #fff; }
.surface-panel--soft { border-color: transparent; background: #f7f8fa; }
</style>
