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
				c_k: [nodes[0].data.spikes, nodes[1].data.spikes, nodes[2].data.spikes],
				div: [0, 0],
				dsv: [0, 0],
				st_next: [1, 1, 1]
			},
			m_pi: [
				[-1, 1, 1],
				[-2, 0, 0]
			],
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

	let testStrings = $state([
		{ value: '11', status: 'idle' },
		{ value: '101', status: 'idle' },
		{ value: '1', status: 'idle' }
	]);

	let timeLimit = $state(100); // Ticks to search before giving up

	function addString() {
		testStrings.push({ value: '', status: 'idle' });
	}

	function removeString(index: number) {
		testStrings.splice(index, 1);
	}

	async function handleJudge() {
		// Clear previous results to force reactivity when new results arrive
		simulation.judgeResults = {};
		
		// Send the batch of strings to the Python iterative engine
		for (let str of testStrings) {
			str.status = 'judging';
			simulation.sendState({
				type: 'judge',
				string: str.value,
				timeLimit: timeLimit,
				state: {
					c_k: [0, 0, 0],
					div: [0],
					dsv: [0],
					st_next: [1, 1, 1]
				},
				m_pi: [
					[-2, 0, 0]
				],
				rule_delays: [0]
			});
		}
	}

	$effect(() => {
		for (let str of testStrings) {
			if (simulation.judgeResults[str.value]) {
				str.status = simulation.judgeResults[str.value];
			}
		}
	});
</script>

<main class="flex h-screen w-screen overflow-hidden">
	<!-- String Computation Sidebar (WebSnapse 4 Everyone) -->
	<aside class="flex w-96 flex-col gap-4 border-r bg-white p-4 shadow-lg z-10 overflow-y-auto">
		<div class="flex items-center justify-between border-b pb-2">
			<h2 class="text-xl font-bold text-gray-800">String Judge</h2>
			<div class="flex items-center gap-2">
				<div class="h-3 w-3 rounded-full {simulation.isConnected ? 'bg-green-500' : 'bg-red-500'}"></div>
				<span class="text-xs font-medium text-gray-600">{simulation.isConnected ? 'Online' : 'Offline'}</span>
			</div>
		</div>

		<!-- Max Search Depth -->
		<div class="flex flex-col gap-1">
			<label for="maxDepth" class="text-sm font-semibold text-gray-700">Max Search Depth (ticks)</label>
			<input 
				id="maxDepth" 
				type="number" 
				bind:value={timeLimit} 
				class="rounded border border-gray-300 p-2 text-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500"
				min="1"
			/>
		</div>

		<!-- Test Strings Table -->
		<div class="flex-1 overflow-y-auto">
			<div class="flex flex-col gap-2">
				<h3 class="text-sm font-semibold text-gray-700">Test Strings</h3>
				{#if testStrings.length === 0}
					<p class="text-sm text-gray-500 italic">No strings added yet.</p>
				{:else}
					<div class="flex flex-col gap-2">
						{#each testStrings as testString, i}
							<div class="flex items-center gap-2 rounded border border-gray-200 bg-gray-50 p-2">
								<input
									type="text"
									bind:value={testString.value}
									placeholder="e.g. 1010"
									class="w-full flex-1 rounded border border-gray-300 px-2 py-1 text-sm focus:border-purple-500 focus:outline-none"
								/>
								<div class="flex items-center justify-center w-20">
									{#if testString.status === 'idle'}
										<span class="text-xs font-medium text-gray-500">Idle</span>
									{:else if testString.status === 'judging'}
										<span class="text-xs font-medium text-blue-500">Judging...</span>
									{:else if testString.status === 'accepted'}
										<span class="text-xs font-bold text-green-600">Accepted</span>
									{:else if testString.status === 'rejected'}
										<span class="text-xs font-bold text-red-600">Rejected</span>
									{/if}
								</div>
								<button
									onclick={() => removeString(i)}
									class="flex h-6 w-6 items-center justify-center rounded bg-red-100 text-red-600 hover:bg-red-200"
									title="Remove"
								>
									&times;
								</button>
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</div>

		<!-- Actions -->
		<div class="flex flex-col gap-2 border-t pt-4">
			<button
				onclick={addString}
				class="w-full rounded border border-purple-600 px-4 py-2 text-sm font-semibold text-purple-600 transition-colors hover:bg-purple-50"
			>
				+ Add String
			</button>
			<button
				onclick={handleJudge}
				class="w-full rounded bg-purple-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-purple-700"
			>
				Judge All
			</button>
		</div>

		<!-- Simulation Controls (Kept for existing functionality) -->
		<div class="border-t mt-2 pt-4">
			<h3 class="text-sm font-semibold text-gray-700 mb-2">Manual Simulation</h3>
			<button
				onclick={handleStep}
				class="w-full rounded bg-gray-800 p-2 font-semibold text-white hover:bg-gray-900 disabled:opacity-50 text-sm"
				disabled={!simulation.isConnected}
			>
				Step Simulation
			</button>
			{#if simulation.possibilities && simulation.possibilities.length > 0}
				<div class="mt-4 flex flex-col gap-2 max-h-40 overflow-y-auto">
					<h3 class="font-bold text-xs text-gray-700">Next State Branches:</h3>
					{#each simulation.possibilities as pos, i}
						<button 
							onclick={() => applyBranch(pos)}
							class="rounded border bg-white p-2 text-left text-xs shadow-sm transition-colors hover:border-purple-500 hover:bg-purple-50"
						>
							<div class="font-bold text-purple-700">Branch {i + 1}</div>
							<div><span class="font-semibold text-gray-600">Spikes:</span> [{pos.c_k.join(', ')}]</div>
							<div><span class="font-semibold text-gray-600">Delay Status:</span> [{pos.dsv.join(', ')}]</div>
						</button>
					{/each}
				</div>
			{/if}
		</div>
	</aside>

	<!-- Visualization Canvas (WebSnapse Reloaded) -->
	<section class="relative flex-1">
		<SvelteFlow {nodes} {edges} {nodeTypes}>
			<Background />
			<Controls />
		</SvelteFlow>
	</section>
</main>
