<script lang="ts">
	import { SvelteFlow, Background, Controls } from '@xyflow/svelte';
	import NeuronNode from '$lib/components/NeuronNode.svelte';
	import { simulation } from '$lib/services/simulation.svelte';
	import { onMount } from 'svelte';
	import '@xyflow/svelte/dist/style.css';

	const nodeTypes = {
		neuron: NeuronNode
	};

	// Svelte 5 Runes for reactive state
	let nodes = $state([
		{
			id: 'n1',
			type: 'neuron',
			position: { x: 150, y: 250 },
			data: {
				id: 'σ₁',
				neuronType: 'input',
				spikes: 2,
				delay: 0,
				rules: ['a^2/a \\to a; 1', 'a \\to \\lambda'] // Mocked LaTeX
			}
		},
		{
			id: 'n2',
			type: 'neuron',
			position: { x: 500, y: 150 },
			data: {
				id: 'σ₂',
				neuronType: 'output',
				spikes: 1,
				delay: 0,
				rules: []
			}
		},
		{
			id: 'n3',
			type: 'neuron',
			position: { x: 500, y: 350 },
			data: {
				id: 'σ₃',
				neuronType: 'output',
				spikes: 3,
				delay: 0,
				rules: []
			}
		}
	]);

	let edges = $state([
		{
			id: 'e1-2',
			source: 'n1',
			target: 'n2',
			animated: true,
			style: 'stroke: #a855f7; stroke-width: 2px;'
		},
		{
			id: 'e1-3',
			source: 'n1',
			target: 'n3',
			animated: true,
			style: 'stroke: #a855f7; stroke-width: 2px;'
		}
	]);

	onMount(() => {
		simulation.connect();
	});

	function handleStep() {
		// Mocked data for Even Positive Integer Generator
		simulation.sendState({
			tick: 0,
			state: {
				c_k: [
					nodes[0].data.spikes,
					nodes[1].data.spikes,
					nodes[2].data.spikes
				],
				div: [0, 0],
				dsv: [0, 0],
				st_next: [1, 1, 1]
			},
			m_pi: [[-1, 1, 1], [-2, 0, 0]],
			stv_k: [0, 0, 0],
			rule_delays: [1, 0],
			rules: []
		});
	}

	function applyBranch(pos) {
		nodes[0].data.spikes = pos.c_k[0];
		nodes[1].data.spikes = pos.c_k[1];
		nodes[2].data.spikes = pos.c_k[2];
		
		// Clear possibilities after selection to represent moving to the next step
		simulation.possibilities = [];
	}
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

		{#if simulation.possibilities && simulation.possibilities.length > 0}
			<div class="mt-4 flex flex-col gap-2">
				<h3 class="font-bold">Next State Branches:</h3>
				<p class="text-xs text-gray-500">Click a branch to apply it to the canvas</p>
				{#each simulation.possibilities as pos, i}
					<button 
						onclick={() => applyBranch(pos)}
						class="rounded border bg-white p-2 text-left text-sm shadow-sm transition-colors hover:border-purple-500 hover:bg-purple-50"
					>
						<div class="font-bold text-purple-700">Branch {i + 1}</div>
						<div><span class="font-semibold text-gray-600">Spikes:</span> [{pos.c_k.join(', ')}]</div>
						<div><span class="font-semibold text-gray-600">Delay Status:</span> [{pos.dsv.join(', ')}]</div>
					</button>
				{/each}
			</div>
		{/if}
	</aside>

	<!-- Visualization Canvas (WebSnapse Reloaded) -->
	<section class="relative flex-1">
		<SvelteFlow {nodes} {edges} {nodeTypes}>
			<Background />
			<Controls />
		</SvelteFlow>
	</section>
</main>
