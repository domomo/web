<script setup>
import { RouterLink } from 'vue-router';

defineProps({
  type: { type: String, default: 'button' },
  variant: { type: String, default: 'primary' },
  disabled: { type: Boolean, default: false },
  href: { type: String, default: '' },
  to: { type: [String, Object], default: null },
});

defineEmits(['click']);
</script>

<template>
  <RouterLink
    v-if="to && !disabled"
    class="brand-button"
    :class="`brand-button--${variant}`"
    :to="to"
  >
    <slot />
  </RouterLink>
  <a
    v-else-if="href"
    class="brand-button"
    :class="`brand-button--${variant}`"
    :href="disabled ? undefined : href"
    :aria-disabled="disabled ? 'true' : undefined"
    :tabindex="disabled ? -1 : undefined"
  >
    <slot />
  </a>
  <span v-else-if="to" class="brand-button" :class="`brand-button--${variant}`" aria-disabled="true" tabindex="-1">
    <slot />
  </span>
  <button
    v-else
    class="brand-button"
    :class="`brand-button--${variant}`"
    :type="type"
    :disabled="disabled"
    @click="$emit('click', $event)"
  >
    <slot />
  </button>
</template>

<style scoped>
.brand-button {
  display: inline-flex;
  min-height: 48px;
  align-items: center;
  justify-content: center;
  padding: 0 20px;
  border: 1px solid transparent;
  border-radius: 12px;
  font: inherit;
  font-size: 15px;
  font-weight: 700;
  text-decoration: none;
  cursor: pointer;
  transition: background-color .16s ease, color .16s ease, border-color .16s ease;
}
.brand-button--primary { background: #0064FF; color: #fff; }
.brand-button--primary:hover:not(:disabled) { background: #0052d4; }
.brand-button--secondary { border-color: #e5eaf2; background: #fff; color: #202938; }
.brand-button--secondary:hover:not(:disabled) { background: #f5f8ff; }
.brand-button:disabled, .brand-button[aria-disabled="true"] { cursor: not-allowed; opacity: .58; }
.brand-button:focus-visible { outline: 3px solid #0064ff55; outline-offset: 3px; }
@media (prefers-reduced-motion: reduce) { .brand-button { transition: none; } }
</style>
