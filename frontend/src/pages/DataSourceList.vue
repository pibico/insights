<template>
	<BasePage>
		<template #header>
			<div class="flex flex-1 justify-between">
				<h1 class="text-3xl font-medium text-gray-900">Data Sources</h1>
				<div>
					<Button appearance="primary" @click="new_dialog = true">
						+ New Data Source
					</Button>
				</div>
			</div>
		</template>
		<template #main>
			<div class="flex flex-1 flex-col space-y-4">
				<div class="flex space-x-4">
					<Input type="text" placeholder="Status" />
				</div>
				<div class="flex h-[calc(100%-1.75rem)] flex-col rounded-md border">
					<!-- List Header -->
					<div
						class="flex items-center justify-between border-b py-3 px-4 text-sm text-gray-500"
					>
						<p class="mr-4">
							<Input type="checkbox" class="rounded-md border-gray-400" />
						</p>
						<p class="flex-1">Title</p>
						<p class="flex-1">Status</p>
						<p class="flex-1">Username</p>
						<p class="flex-1">Database Type</p>
						<p class="flex-1 text-right">Last Modified</p>
					</div>
					<ul
						role="list"
						class="flex flex-1 flex-col divide-y divide-gray-200 overflow-y-scroll"
					>
						<li v-for="source in dataSources" :key="source.name">
							<a
								class="flex cursor-pointer items-center rounded-md py-3 px-4 hover:bg-gray-50"
							>
								<p class="mr-4">
									<Input type="checkbox" class="rounded-md border-gray-400" />
								</p>
								<p
									class="flex-1 whitespace-nowrap text-sm font-medium text-gray-900"
								>
									{{ source.title }}
								</p>
								<p class="flex-1 whitespace-nowrap text-sm text-gray-500">
									<Badge
										:color="source.status == 'Inactive' ? 'yellow' : 'green'"
									>
										{{ source.status }}
									</Badge>
								</p>
								<p class="flex-1 whitespace-nowrap text-sm text-gray-500">
									{{ source.username }}
								</p>
								<p class="flex-1 whitespace-nowrap text-sm text-gray-500">
									{{ source.database_type }}
								</p>
								<p
									class="flex-1 text-right text-sm text-gray-500"
									:title="source.modified"
								>
									{{ source.modified_from_now }}
								</p>
							</a>
						</li>
					</ul>
					<div class="flex w-full border-t px-4 py-2 text-sm text-gray-500">
						<p class="ml-auto">
							Showing {{ dataSources.length }} of {{ dataSources.length }}
						</p>
					</div>
				</div>
			</div>
		</template>
	</BasePage>

	<Dialog :options="{ title: 'New Data Source' }" v-model="new_dialog">
		<template #body-content>
			<div class="text-sm text-gray-400">Not implemented yet</div>
		</template>
	</Dialog>
</template>

<script setup>
import BasePage from '@/components/BasePage.vue'
import { Badge, createResource } from 'frappe-ui'
import { updateDocumentTitle } from '@/utils/document'

import moment from 'moment'
import { computed, ref } from 'vue'

const new_dialog = ref(false)

const getDataSources = createResource({
	method: 'insights.api.get_data_sources',
	initialData: [],
})
getDataSources.fetch()

const dataSources = computed(() => {
	return getDataSources.data.map((source) => {
		source.modified_from_now = moment(source.modified).fromNow()
		return source
	})
})

const pageMeta = ref({
	title: 'Data Sources',
})
updateDocumentTitle(pageMeta)
</script>
