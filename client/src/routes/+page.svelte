<script lang="ts">
	import { SvelteFlow, Background, Controls } from '@xyflow/svelte';
	import { simulation } from '$lib/services/simulation.svelte';
	import { onMount } from 'svelte';
	import '@xyflow/svelte/dist/style.css';

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

	onMount(() => {
		simulation.connect();
	});

	function handleStep() {
		// Mock payload based on the Even Positive Integer Generator case
		const payload = {
			tick: 0,
			state: { c_k: [2, 1, 3], div: [0, 0], dsv: [0, 0], st_next: [1, 1, 1] },
			m_pi: [
				[-1, 1, 1],
				[-2, 0, 0]
			],
			stv_k: [0, 0, 0],
			rule_delays: [1, 0]
		};
		simulation.sendState(payload);
	}

	// Effect to update nodes when server sends new possibilities
	$effect(() => {
		if (simulation.possibilities.length > 0) {
			const next = simulation.possibilities[0]; // Auto-pick first branch for now
			nodes[0].data.label = `n1: ${next.c_k[0]} spikes (Delay: ${next.dsv[0]})`;
			nodes[1].data.label = `n2: ${next.c_k[1]} spikes`;
			nodes[2].data.label = `n3: ${next.c_k[2]} spikes`;
		}
	});
</script>

<main class="flex h-screen w-screen overflow-hidden">
	<!-- String Computation Sidebar (WebSnapse 4 Everyone) -->
	<aside class="flex w-80 flex-col gap-4 border-r bg-gray-50 p-4">
		<h2 class="text-xl font-bold">String Computation</h2>
		<div class="flex items-center gap-2">
			<div
				class="h-3 w-3 rounded-full {simulation.isConnected ? 'bg-green-500' : 'bg-red-500'}"
			></div>
			<span class="text-sm">{simulation.isConnected ? 'Engine Online' : 'Engine Offline'}</span>
		</div>
		<button
			onclick={handleStep}
			class="rounded bg-purple-600 p-2 font-semibold text-white hover:bg-purple-700 disabled:opacity-50"
			disabled={!simulation.isConnected}
		>
			Step Simulation
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
