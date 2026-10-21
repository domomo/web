<script setup>
import BrandButton from './BrandButton.vue';

defineProps({
  eyebrow: { type: String, default: '' },
  title: { type: String, required: true },
  description: { type: String, default: '' },
  image: { type: String, default: '' },
  imageAlt: { type: String, default: '' },
  features: { type: Array, default: () => [] },
  actionLabel: { type: String, default: '시작하기' },
  actionHref: { type: String, default: '' },
  showAction: { type: Boolean, default: true },
  actionDisabled: { type: Boolean, default: false },
});

defineEmits(['action']);
</script>

<template>
  <article class="product-detail" :class="{ 'product-detail--visual': image || $slots.visual }">
    <div class="product-detail__copy">
      <p v-if="eyebrow" class="product-detail__eyebrow">{{ eyebrow }}</p>
      <h2>{{ title }}</h2>
      <slot name="description">
        <p v-if="description" class="product-detail__description">{{ description }}</p>
      </slot>
      <slot name="content" />
      <ul v-if="features.length" class="product-detail__features">
        <li v-for="feature in features" :key="feature">{{ feature }}</li>
      </ul>
      <div v-if="showAction" class="product-detail__action">
        <slot name="action">
          <BrandButton v-if="actionHref" :href="actionHref" :disabled="actionDisabled">{{ actionLabel }}</BrandButton>
          <BrandButton v-else :disabled="actionDisabled" @click="$emit('action')">{{ actionLabel }}</BrandButton>
        </slot>
      </div>
      <slot name="below-action" />
    </div>
    <div v-if="image || $slots.visual" class="product-detail__visual">
      <slot name="visual">
        <img :src="image" :alt="imageAlt" />
      </slot>
    </div>
  </article>
</template>

<style scoped>
.product-detail { display: grid; grid-template-columns: minmax(0, 1fr); align-items: center; gap: 32px; padding: clamp(26px, 5vw, 54px); border: 1px solid #e5e8eb; border-radius: 22px; background: #fff; }
.product-detail--visual { grid-template-columns: minmax(0, 1fr) minmax(220px, .62fr); gap: clamp(30px, 6vw, 70px); }
.product-detail__copy { max-width: 540px; }
.product-detail__eyebrow { margin: 0 0 14px; color: #0064FF; font-size: 14px; font-weight: 750; }
.product-detail h2 { margin: 0; color: #172333; font-size: clamp(29px, 4vw, 44px); line-height: 1.24; letter-spacing: -1.7px; text-wrap: balance; }
.product-detail__description { margin: 18px 0 0; color: #5d6a7c; font-size: 16px; line-height: 1.8; }
.product-detail__features { display: grid; gap: 12px; margin: 22px 0 28px; padding: 0; list-style: none; color: #364355; font-size: 14px; }
.product-detail__features li { display: flex; align-items: flex-start; gap: 10px; }
.product-detail__features li::before { width: 19px; height: 19px; flex: none; border-radius: 50%; background: #dceaff; color: #0064FF; content: '✓'; font-size: 12px; font-weight: 800; line-height: 19px; text-align: center; }
.product-detail__action { margin-top: 24px; }
.product-detail__visual { display: grid; min-height: 240px; place-items: center; overflow: hidden; border-radius: 22px; background: #e5efff; }
.product-detail__visual img { display: block; width: 100%; height: 100%; max-height: 360px; object-fit: cover; }
@media (max-width: 700px) { .product-detail--visual { grid-template-columns: 1fr; gap: 30px; } .product-detail__visual { min-height: 190px; grid-row: 1; } }
</style>
