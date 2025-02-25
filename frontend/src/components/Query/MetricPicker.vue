<template>
	<div class="flex flex-col space-y-3">
		<div class="space-y-1 text-sm text-gray-600">
			<div class="font-light">Type</div>
			<Autocomplete
				v-model="metric.type"
				:options="typeOptions"
				placeholder="Select metric type..."
				@selectOption="onTypeSelect"
			/>
		</div>
		<div v-if="columnNeeded" class="space-y-1 text-sm text-gray-600">
			<div class="font-light">Column</div>
			<Autocomplete
				v-model="metric.column"
				:options="filteredColumns"
				placeholder="Select a column..."
				@selectOption="onColumnSelect"
			/>
		</div>
		<div v-if="metric.label" class="space-y-1 text-sm text-gray-600">
			<div class="font-light">Label</div>
			<Input
				type="text"
				v-model="metric.label"
				class="h-8 placeholder:text-sm"
				placeholder="Enter a label..."
			/>
		</div>
		<div class="flex justify-end space-x-2">
			<Button v-if="row_name" class="text-red-500" appearance="white" @click="removeMetric">
				Remove
			</Button>
			<Button @click="addMetric" appearance="primary" :disabled="addDisabled">
				{{ row_name ? 'Update' : 'Add ' }}
			</Button>
		</div>
	</div>
</template>

<script setup>
import { isEmptyObj } from '@/utils'
import Autocomplete from '@/components/Autocomplete.vue'

import { computed, inject, onMounted, reactive, ref, watch } from 'vue'

const query = inject('query')

const emit = defineEmits(['column-select', 'close'])
const props = defineProps({
	column: {
		type: Object,
		default: {},
	},
})

const typeOptions = ref([
	{
		label: 'Count of records',
		value: 'Count',
	},
	{
		label: 'Sum of',
		value: 'Sum',
	},
	{
		label: 'Avg of',
		value: 'Avg',
	},
])
const metric = reactive({
	// since props.column comes from doc.columns, it doesn't have value property
	column: { ...props.column, value: props.column.column },
	label: props.column.label,
	type: typeOptions.value.find((t) => {
		return t.value == props.column.aggregation
	}),
})
// for editing a metric
const row_name = ref(props.column.name)

const columnNeeded = computed(() => {
	return !isEmptyObj(metric.type) && metric.type.value !== 'Count'
})
const addDisabled = computed(() => {
	return (
		isEmptyObj(metric.type) ||
		(columnNeeded.value && isEmptyObj(metric.column)) ||
		!metric.label
	)
})

onMounted(() => query.fetchColumns())
const columnOptions = computed(() => {
	return query.fetchColumnsData.value?.map((c) => {
		return {
			...c,
			value: c.column,
			description: c.table_label,
		}
	})
})
const filteredColumns = computed(() => {
	if (isEmptyObj(metric.type)) {
		return []
	}
	if (metric.type.value === 'Sum' || metric.type.value === 'Avg') {
		return columnOptions.value?.filter((c) => query.NUMBER_FIELD_TYPES.includes(c.type))
	}
})

watch(
	() => metric.type,
	(type) => (metric.column = {})
)

function onTypeSelect(option) {
	metric.type = option ? option : {}
	if (metric.type.label) {
		metric.label = metric.type.label + ' '
	}
}
function onColumnSelect(option) {
	metric.column = option ? option : {}
	metric.column.name = row_name.value
}

function addMetric() {
	if (isEmptyObj(metric.type)) {
		return
	}
	if (columnNeeded.value && isEmptyObj(metric.column)) {
		return
	}

	if (!columnNeeded.value) {
		if (!isEmptyObj(props.column)) {
			// edit
			props.column.label = metric.label
			props.column.aggregation = metric.type.value
			emit('column-select', props.column)
		} else {
			// add
			emit('column-select', makeCountColumn())
		}
	}

	if (columnNeeded.value) {
		metric.column.aggregation = metric.type.value
		emit('column-select', metric.column)
	}
}
function makeCountColumn() {
	const table = query.tables[0]
	return {
		type: 'Int',
		column: 'name',
		table: table.table,
		label: metric.label,
		table_label: table.label,
		aggregation: metric.type.value,
	}
}
function removeMetric() {
	query.removeColumn({ column: metric.column })
	emit('close')
}
</script>
