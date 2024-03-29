<script setup lang="ts">
import { computed } from 'vue'
import { useField, useForm } from 'vee-validate'
import { boolean, number, object } from 'yup'
import Dialog from 'primevue/dialog'
import Button from 'primevue/button'
import Dropdown from 'primevue/dropdown'
import InputNumber from 'primevue/inputnumber'
import RadioButton from 'primevue/radiobutton'
import { useToast } from 'primevue/usetoast'

import type { CategoriesList } from '@api/categories/categories'
import { createFastPayout } from '@api/payouts/fast-payouts'

const props = defineProps<{
  modelValue: boolean
  categories: CategoriesList
}>()

const emits = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'fastRecordCreated'): void
}>()

const dialogValue = computed({
  get() {
    return props.modelValue
  },
  set(newValue: boolean) {
    emits('update:modelValue', newValue)
  },
})

const schema = object({
  category: number().required('Обязательное поле'),
  amount: number().required('Обязательное поле'),
  isExpense: boolean().required('Обязательное поле'),
})

const { handleSubmit } = useForm({
  validationSchema: schema,
  initialValues: {
    category: undefined,
    amount: undefined,
    isExpense: false,
  },
})

const { value: category, errorMessage: categoryError } = useField<number>('category')
const { value: amount, errorMessage: amountError } = useField<number>('amount')
const { value: isExpense } = useField<boolean>('isExpense')

const toast = useToast()
const onSubmit = handleSubmit(async(values, { resetForm }) => {
  if (!schema.isValidSync(values)) return

  const result = await createFastPayout(values)
  if (result.isRight()) {
    toast.add({ severity: 'success', summary: 'Успешно', detail: 'Быстрая запись создана', life: 3000 })
    resetForm()
    emits('update:modelValue', false)
    emits('fastRecordCreated')
    return
  }

  toast.add({ severity: 'error', summary: 'Ошибка', detail: 'Ошибка при создании быстрой записи', life: 3000 })
})
</script>
<template>
  <Dialog v-model:visible="dialogValue" header="Добавьте новую быструю запись" class="modal border-rounded" modal dismissable-mask>
    <form class="flex flex-column" @submit.prevent="onSubmit">
      <div class="mb-5">
        <Dropdown id="category" v-model="category" class="w-full" :options="categories" option-label="title" option-value="id" name="category" placeholder="Категория" filter />
        <div class="p-error mt-1 h-1rem text-sm">
          {{ categoryError }}
        </div>
      </div>
      <div class="mb-5">
        <InputNumber id="amount" v-model="amount" class="w-full" name="amount" placeholder="Сумма" />
        <div class="p-error mt-1 h-1rem text-sm">
          {{ amountError }}
        </div>
      </div>
      <div class="mb-5 flex align-items-center justify-content-evenly">
        <div>
          <RadioButton id="income" v-model="isExpense" class="mr-2" name="type" :value="false" />
          <label for="income">Доход</label>
        </div>
        <div>
          <RadioButton id="expense" v-model="isExpense" class="mr-2" name="type" :value="true" />
          <label for="expense">Расход</label>
        </div>
      </div>
      <Button label="СОЗДАТЬ" class="p-button-rounded p-button-sm align-self-center" type="submit" />
    </form>
  </Dialog>
</template>
<style lang="scss">
@import 'primeflex/primeflex.scss';

.p-dialog {
  @include styleclass('p-4 bg-white border-round w-50');
}
.p-dialog-titlebar {
  @include styleclass('text-center');
}
.p-dialog-titlebar-icon {
  @include styleclass('mr-4')
}
</style>
