<script setup>
import BrandButton from './BrandButton.vue';

defineProps({
  title: { type: String, required: true },
  description: { type: String, required: true },
  category: { type: String, default: '' },
  icon: { type: String, default: '' },
  href: { type: String, default: '' },
  to: { type: [String, Object], default: null },
  actionLabel: { type: String, default: '자세히 보기' },
});
</script>

<template>
  <article class="service-card">
    <div class="service-card__top">
      <span v-if="icon" class="service-card__icon" aria-hidden="true">{{ icon }}</span>
      <span v-if="category" class="service-card__category">{{ category }}</span>
    </div>
    <h3>{{ title }}</h3>
    <p>{{ description }}</p>
    <BrandButton v-if="href || to" :href="href" :to="to" variant="secondary">{{ actionLabel }}</BrandButton>
    <slot name="action" />
  </article>
</template>

<style scoped>
.service-card { display: flex; min-height: 228px; flex-direction: column; align-items: flex-start; padding: 24px; border: 1px solid #e8edf4; border-radius: 18px; background: #fff; }
.service-card__top { display: flex; width: 100%; align-items: center; justify-content: space-between; gap: 12px; }
.service-card__icon { display: grid; width: 48px; height: 48px; place-items: center; border-radius: 15px; background: #edf4ff; color: #0064FF; font-size: 21px; font-weight: 750; }
.service-card__category { color: #758195; font-size: 12px; font-weight: 650; }
.service-card h3 { margin: 22px 0 8px; color: #202a38; font-size: 19px; letter-spacing: -.4px; }
.service-card p { flex: 1; margin: 0 0 20px; color: #657184; font-size: 14px; line-height: 1.7; }
</style>
