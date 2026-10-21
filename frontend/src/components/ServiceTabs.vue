<script setup>
defineProps({
  tabs: { type: Array, required: true },
  modelValue: { type: String, default: '' },
  label: { type: String, default: '서비스 분류' },
  variant: { type: String, default: 'underline', validator: (value) => ['underline', 'pills', 'segmented'].includes(value) },
});

const emit = defineEmits(['update:modelValue', 'change']);

function selectTab(tab) {
  emit('update:modelValue', tab.value);
  emit('change', tab.value);
}

function handleKeydown(event, index, tabs) {
  let nextIndex = index;
  if (event.key === 'ArrowRight') nextIndex = (index + 1) % tabs.length;
  else if (event.key === 'ArrowLeft') nextIndex = (index - 1 + tabs.length) % tabs.length;
  else if (event.key === 'Home') nextIndex = 0;
  else if (event.key === 'End') nextIndex = tabs.length - 1;
  else return;

  event.preventDefault();
  const tab = tabs[nextIndex];
  event.currentTarget.parentElement.querySelectorAll('[role="tab"]')[nextIndex]?.focus();
  selectTab(tab);
}
</script>

<template>
  <div class="service-tabs" :class="`service-tabs--${variant}`" role="tablist" :aria-label="label">
    <button
      v-for="tab in tabs"
      :key="tab.value"
      class="service-tabs__tab"
      :class="{ 'is-active': modelValue === tab.value }"
      type="button"
      role="tab"
      :tabindex="modelValue === tab.value ? 0 : -1"
      :aria-selected="modelValue === tab.value"
      @click="selectTab(tab)"
      @keydown="handleKeydown($event, tabs.indexOf(tab), tabs)"
    >
      {{ tab.label }}
    </button>
  </div>
</template>

<style scoped>
.service-tabs { display: flex; flex-wrap: wrap; gap: 8px; border-bottom: 1px solid #e9edf3; }
.service-tabs__tab { position: relative; min-height: 48px; padding: 0 16px; border: 0; background: transparent; color: #667386; font: inherit; font-size: 15px; font-weight: 650; cursor: pointer; }
.service-tabs__tab::after { position: absolute; right: 12px; bottom: -1px; left: 12px; height: 3px; border-radius: 3px 3px 0 0; background: transparent; content: ''; }
.service-tabs__tab:hover { color: #0064FF; }
.service-tabs__tab.is-active { color: #0064FF; }
.service-tabs__tab.is-active::after { background: #0064FF; }
.service-tabs__tab:focus-visible { outline: 2px solid #0064FF; outline-offset: -3px; }
.service-tabs--pills { gap: 8px; overflow-x: auto; border: 0; padding: 0 0 8px; }
.service-tabs--pills .service-tabs__tab { min-height: 40px; flex: none; padding: 0 16px; border: 1px solid #e8ebef; border-radius: 22px; background: #fff; color: #596575; font-size: 13px; }
.service-tabs--pills .service-tabs__tab::after { display: none; }
.service-tabs--pills .service-tabs__tab.is-active { border-color: #0064FF; background: #0064FF; color: #fff; }
.service-tabs--segmented { width: fit-content; gap: 5px; margin: 4px 0 18px; padding: 4px; border: 0; border-radius: 12px; background: #f2f4f7; }
.service-tabs--segmented .service-tabs__tab { min-height: 36px; padding: 0 17px; border-radius: 9px; color: #697586; font-size: 13px; }
.service-tabs--segmented .service-tabs__tab::after { display: none; }
.service-tabs--segmented .service-tabs__tab.is-active { background: #fff; color: #0064FF; box-shadow: 0 1px 4px #1822301a; }
</style>
