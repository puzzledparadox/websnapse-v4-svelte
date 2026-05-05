<script lang="ts">
	import { SvelteFlow, Background, Controls } from '@xyflow/svelte';

	// Svelte 5 Runes for reactive state
	let nodes = $state([
		{ id: '1', position: { x: 0, y: 0 }, data: { label: 'n1: 2 spikes' } },
		{ id: '2', position: { x: 200, y: -100 }, data: { label: 'n2: 1 spike' } },
		{ id: '3', position: { x: 200, y: 100 }, data: { label: 'n3: 3 spikes' } }
	]);
	let edges = $state([
		{ id: 'e1-2', source: '1', target: '2' },
		{ id: 'e1-3', source: '1', target: '3' }
	]);
</script>

<main class="flex h-screen w-screen overflow-hidden">
	<!-- String Computation Sidebar (WebSnapse 4 Everyone) -->
	<aside class="flex w-80 flex-col gap-4 border-r bg-gray-50 p-4">
		<h2 class="text-xl font-bold">String Computation</h2>
		<div class="bg-whitep-2 flex-1 rounded border text-sm text-gray-500">
			Input strings to judge...
		</div>
		<button class="rounded bg-purple-600 py-2 font-semibold text-white hover:bg-purple-700">
			Judge
		</button>
	</aside>

	<!-- Visualization Canvas (WebSnapse Reloaded) -->
	<section class="relative flex-1">
		<SvelteFlow {nodes} {edges}>
			<Background />
			<Controls />
		</SvelteFlow>
	</section>
</main>
