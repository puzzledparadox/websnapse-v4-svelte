<script lang="ts">
	import { Handle, Position } from '@xyflow/svelte';
	import Katex from 'svelte-katex';
	import 'katex/dist/katex.min.css';

	// Svelte 5 approach for receiving node data
	let { data } = $props();

	let isInput = $derived(data.neuronType === 'input' || data.neuronType === 'Input');
	let isOutput = $derived(data.neuronType === 'output' || data.neuronType === 'Output');
	let isClosed = $derived(data.delay > 0);
	let isActive = $derived(data.previewFiring !== undefined ? !!data.previewFiring : !!data.isFiring);

	let borderColorClass = $derived(
		isActive
			? 'border-purple-500 ring-2 ring-purple-300/60'
			: isClosed
				? 'border-red-500 ring-2 ring-red-200'
				: isInput
					? 'border-emerald-500'
					: isOutput
						? 'border-amber-500'
						: 'border-slate-300'
	);

	let glowStyle = $derived(
		isActive
			? 'box-shadow: 0 0 16px 4px rgba(168, 85, 247, 0.4);'
			: isClosed
				? 'box-shadow: 0 0 12px 2px rgba(239, 68, 68, 0.25);'
				: ''
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

	function formatSpikeTrain(train: string | number | undefined): string {
		if (train === undefined || train === null) return '';
		const str = String(train);
		if (!str) return '';
		
		let result: string[] = [];
		let currentChar = str[0];
		let count = 1;
		
		for (let i = 1; i <= str.length; i++) {
			if (i < str.length && str[i] === currentChar) {
				count++;
			} else {
				if (count > 1) {
					result.push(`${currentChar}^{${count}}`);
				} else {
					result.push(`${currentChar}`);
				}
				if (i < str.length) {
					currentChar = str[i];
					count = 1;
				}
			}
		}
		return result.join('\\ ');
	}
</script>

<!-- Neuron visual container -->
<div
	class="relative min-w-[120px] rounded-xl border-2 bg-white px-4 py-2 shadow-md transition-all duration-300 {borderColorClass}"
	style={glowStyle}
>
	{#if isInput || isOutput}
		<div
			class="absolute -top-3 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider {badgeBgClass}"
		>
			{isInput ? 'Input' : 'Output'}
		</div>
	{/if}

	<!-- Top: Neuron ID and Spike Count -->
	<div class="mb-2 flex items-center justify-between gap-2 border-b pb-1 pt-1">
		<span class="font-mono text-xs text-gray-400">{data.id}</span>
		<span class="text-lg font-bold {spikeColorClass}">
			{#if isInput || isOutput}
				{#key data.spikes}
					<Katex>{formatSpikeTrain(data.spikes)}</Katex>
				{/key}
			{:else}
				{data.spikes}
			{/if}
		</span>
	</div>

	<!-- Center: Spiking Rules -->
	{#if !isInput && !isOutput}
		<div class="flex flex-col gap-1 py-2 text-center text-sm">
			{#each data.rules || [] as rule}
				{#key rule}
					<Katex>{rule}</Katex>
				{/key}
			{/each}
		</div>
	{/if}

	<!-- Bottom: Delay counter (always shown for regular nodes) -->
	{#if !isInput && !isOutput}
		<div class="mt-1 text-center text-[10px] font-bold uppercase tracking-tighter {isClosed ? 'text-red-600' : 'text-slate-400'}">
			{#if isClosed}
				Closed ({data.delay})
			{:else}
				Open
			{/if}
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
