<template>
	<div class="flex h-full w-full flex-1 px-1 py-4">
		<div
			class="flex h-full w-72 flex-shrink-0 flex-col space-y-3 overflow-y-scroll border-r pr-4"
		>
			<div class="space-y-2 text-gray-600">
				<div class="text-base font-light text-gray-500">Title</div>
				<Input
					type="text"
					placeholder="Enter a suitable title..."
					v-model="visualization.title"
				/>
			</div>
			<div class="space-y-2">
				<div class="text-base font-light text-gray-500">Select Visualization Type</div>
				<div class="-ml-1 grid grid-cols-[repeat(auto-fill,3.5rem)] gap-3">
					<div
						class="flex flex-col items-center space-y-1 text-gray-500"
						:class="{
							'cursor-pointer hover:text-gray-600': !invalidVizTypes.includes(
								viz.type
							),
							'cursor-not-allowed hover:text-gray-500': invalidVizTypes.includes(
								viz.type
							),
						}"
						v-for="(viz, i) in visualizationTypes"
						:key="i"
						@click="setVizType(viz.type)"
					>
						<div
							class="flex h-12 w-12 items-center justify-center rounded-md border border-gray-200 bg-white hover:shadow"
							:class="{
								' border-blue-300 text-blue-500 shadow-sm hover:shadow-sm':
									viz.type == visualization.type,
								' border-dashed border-gray-300 opacity-60 hover:shadow-none':
									invalidVizTypes.includes(viz.type),
							}"
						>
							<FeatherIcon :name="viz.icon" class="h-6 w-6" />
						</div>
						<span
							class="text-sm"
							:class="{
								'font-normal text-blue-600': viz.type == visualization.type,
								'font-light': viz.type != visualization.type,
								'opacity-60': invalidVizTypes.includes(viz.type),
							}"
						>
							{{ viz.type }}
						</span>
					</div>
				</div>
			</div>
			<!-- Visualization Data Fields -->
			<div v-if="visualization.dataSchema.labelColumn" class="space-y-2 text-gray-600">
				<div class="text-base font-light text-gray-500">Select Dimension</div>
				<Autocomplete v-model="visualization.data.labelColumn" :options="labelColumns" />
			</div>
			<div v-if="visualization.dataSchema.valueColumn" class="space-y-2 text-gray-600">
				<div class="text-base font-light text-gray-500">Select Measure</div>
				<Autocomplete v-model="visualization.data.valueColumn" :options="valueColumns" />
			</div>
			<div v-if="visualization.dataSchema.pivotColumn" class="space-y-2 text-gray-600">
				<div class="text-base font-light text-gray-500">Select Column</div>
				<Autocomplete v-model="visualization.data.pivotColumn" :options="labelColumns" />
			</div>
			<Button
				appearance="primary"
				@click="saveVisualization"
				:loading="visualization.savingDoc"
			>
				Save Changes
			</Button>
		</div>
		<div class="flex w-[calc(100%-18rem)] pl-4">
			<component
				v-if="visualization.component && visualization.componentProps"
				:is="visualization.component"
				v-bind="visualization.componentProps"
			></component>
		</div>
	</div>
</template>

<script setup>
import Autocomplete from '@/components/Autocomplete.vue'

import { computed, inject } from 'vue'
import { useVisualization, visualizationTypes } from '@/controllers/visualization'

const query = inject('query')
const visualizationID = query.visualizations.value[0]
const visualization = useVisualization({ visualizationID, query })

const invalidVizTypes = computed(() => {
	// TODO: change based on data
	return ['Funnel', 'Row']
})
const setVizType = (type) => {
	if (!invalidVizTypes.value.includes(type)) {
		visualization.type = type
		visualization.data = {}
	}
}

const labelColumns = computed(() => {
	return query.columns
		.filter((c) => c.aggregation == 'Group By')
		.map((c) => {
			return {
				label: c.label,
				value: c.value,
			}
		})
})
const valueColumns = computed(() => {
	return query.columns
		.filter((c) => c.aggregation != 'Group By')
		.map((c) => {
			return {
				label: c.label,
				value: c.value,
			}
		})
})

const $notify = inject('$notify')
const saveVisualization = () => {
	const onSuccess = () => {
		$notify({
			title: 'Visualization Saved',
			appearance: 'success',
		})
	}
	visualization.updateDoc({ onSuccess })
}
</script>
