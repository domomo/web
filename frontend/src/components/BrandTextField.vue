<script setup>
defineOptions({ inheritAttrs: false });

defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, required: true },
  name: { type: String, required: true },
  id: { type: String, default: '' },
  type: { type: String, default: 'text' },
  placeholder: { type: String, default: '' },
  autocomplete: { type: String, default: '' },
  error: { type: String, default: '' },
  required: { type: Boolean, default: false },
});

defineEmits(['update:modelValue']);
</script>

<template>
  <div class="brand-field">
    <label :for="id || `field-${name}`">{{ label }}</label>
    <input
      :id="id || `field-${name}`"
      v-bind="$attrs"
      :name="name"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :autocomplete="autocomplete || undefined"
      :required="required"
      :aria-invalid="error ? 'true' : undefined"
      :aria-describedby="error ? `error-${id || name}` : undefined"
      @input="$emit('update:modelValue', $event.target.value)"
    />
    <p v-if="error" :id="`error-${id || name}`" class="brand-field__error" role="alert">{{ error }}</p>
  </div>
</template>

<style scoped>
.brand-field { display: grid; gap: 8px; }
.brand-field label { color: #303b4b; font-size: 14px; font-weight: 650; }
.brand-field input { width: 100%; min-height: 50px; padding: 0 15px; border: 1px solid #d9e0e9; border-radius: 11px; background: #fff; color: #191f28; font: inherit; font-size: 15px; transition: border-color .14s, box-shadow .14s; }
.brand-field input::placeholder { color: #a4adba; }
.brand-field input:focus-visible { border-color: #0064FF; outline: 0; box-shadow: 0 0 0 3px #0064ff20; }
.brand-field input[aria-invalid="true"] { border-color: #d64545; }
.brand-field__error { margin: 0; color: #c03939; font-size: 13px; line-height: 1.5; }
</style>
