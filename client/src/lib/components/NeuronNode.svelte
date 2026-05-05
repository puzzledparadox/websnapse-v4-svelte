<script lang="ts">
	import { Handle, Position } from '@xyflow/svelte';
	import Katex from 'svelte-katex';
	import 'katex/dist/katex.min.css';

	// Svelte 5 approach for receiving node data
	let { data } = $props();

	let isInput = $derived(data.neuronType === 'input' || data.neuronType === 'Input');
	let isOutput = $derived(data.neuronType === 'output' || data.neuronType === 'Output');

	let borderColorClass = $derived(
		data.delay > 0
			? 'border-red-500 ring-2 ring-red-200'
			: isInput
				? 'border-emerald-500'
				: isOutput
					? 'border-amber-500'
					: 'border-purple-500'
	);

	let spikeColorClass = $derived(
		isInput ? 'text-emerald-700' : isOutput ? 'text-amber-700' : 'text-purple-700'
	);

	let handleColorClass = $derived(
		isInput ? '!bg-emerald-500' : isOutput ? '!bg-amber-500' : '!bg-purple-500'
	);

	let badgeBgClass = $derived(
		isInput
			? 'bg-emerald-100 text-emerald-800 border-emerald-200'
			: isOutput
				? 'bg-amber-100 text-amber-800 border-amber-200'
				: ''
	);
</script>

<!-- Neuron visual container -->
<div
	class="relative min-w-[120px] rounded-xl border-2 bg-white px-4 py-2 shadow-md transition-all {borderColorClass}"
>
	{#if isInput || isOutput}
		<div
			class="absolute -top-3 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider {badgeBgClass}"
		>
			{isInput ? 'Input' : 'Output'}
		</div>
	{/if}

	<!-- Top: Neuron ID and Spike Count -->
	<div class="mb-2 flex items-center justify-between border-b pb-1 pt-1">
		<span class="font-mono text-xs text-gray-400">{data.id}</span>
		<span class="text-lg font-bold {spikeColorClass}">{data.spikes}</span>
	</div>

	<!-- Center: Spiking Rules -->
	<div class="flex flex-col gap-1 py-2 text-center text-sm">
		{#each data.rules || [] as rule}
			<Katex>{rule}</Katex>
		{/each}
	</div>

	<!-- Bottom: Delay Status (Algorithm 4) -->
	{#if data.delay > 0}
		<div class="mt-1 text-center text-[10px] font-bold uppercase tracking-tighter text-red-600">
			Closed ({data.delay})
		</div>
	{/if}

	<!-- Connections points for Synapses -->
	{#if !isInput}
		<Handle type="target" position={Position.Left} class="h-2 w-2 {handleColorClass}" />
	{/if}
	{#if !isOutput}
		<Handle type="source" position={Position.Right} class="h-2 w-2 {handleColorClass}" />
	{/if}
</div>
