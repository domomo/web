<script setup>
defineProps({
  kicker: { type: String, default: '' },
  title: { type: String, required: true },
  description: { type: String, default: '' },
  titleId: { type: String, default: '' },
  titleTag: { type: String, default: 'h1', validator: (value) => ['h1', 'h2', 'h3'].includes(value) },
  variant: { type: String, default: 'default', validator: (value) => ['default', 'section'].includes(value) },
});
</script>

<template>
  <header class="page-heading" :class="`page-heading--${variant}`">
    <div>
      <p v-if="kicker" class="page-kicker">{{ kicker }}</p>
      <component :is="titleTag" :id="titleId || undefined">{{ title }}</component>
      <p v-if="description" class="page-intro">{{ description }}</p>
    </div>
    <div v-if="$slots.trailing" class="page-heading__trailing"><slot name="trailing" /></div>
  </header>
</template>

<style scoped>
.page-heading { display: flex; align-items: end; justify-content: space-between; gap: 24px; margin: 48px 0 28px; }
.page-heading h1, .page-heading h2, .page-heading h3 { margin: 0; color: #191f28; font-size: clamp(30px, 4vw, 42px); font-weight: 700; line-height: 1.3; letter-spacing: -1.5px; text-wrap: balance; }
.page-heading--section h2 { font-size: 24px; letter-spacing: -.8px; }
.page-kicker { margin: 0 0 9px; color: #0064FF; font-size: 13px; font-weight: 650; }
.page-intro { margin: 10px 0 0; color: #6b7684; font-size: 14px; line-height: 1.8; }
.page-heading__trailing { flex: none; }
@media (max-width: 560px) { .page-heading { align-items: flex-start; margin: 32px 0 22px; } .page-heading h1 { font-size: 30px; } .page-heading--section h2 { font-size: 21px; } }
</style>
