<!--
	@component
	NeuronNode.svelte
	
	The core visual representation of an SN P system neuron within Svelte Flow.
	Displays the neuron's ID, current spike count (rendered via KaTeX), active rules,
	and dynamic styling indicating its state (open, closed, or actively firing).
	Supports distinct styles for input, output, and regular neurons.
-->
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

	let stateClass = $derived(
		isActive ? 'is-active' :
		isClosed ? 'is-closed' :
		isInput ? 'is-input' :
		isOutput ? 'is-output' : ''
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

	/**
	 * Formats a raw spike train string into a condensed LaTeX representation.
	 * Groups identical consecutive characters into exponents.
	 * Example: '11100' becomes '1^{3}\ 0^{2}'
	 * 
	 * @param train - The raw string or number representing the spikes.
	 * @returns The condensed string formatted for KaTeX rendering.
	 */
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
	class="neuron-node {stateClass} relative min-w-[120px] rounded-xl border-2 bg-white px-4 py-2 shadow-md transition-[border-color,box-shadow,transform] duration-300"
>
	{#if isInput || isOutput}
		<div
			class="absolute -top-3 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider {badgeBgClass}"
		>
			{isInput ? 'Input' : 'Output'}
		</div>
	{:else if isClosed}
		<!-- Closed/delay countdown badge -->
		<div class="delay-badge">
			<svg xmlns="http://www.w3.org/2000/svg" width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
			{data.delay}
		</div>
	{/if}

	<!-- Top: Neuron ID and Spike Count -->
	<div class="mb-2 flex items-center justify-between gap-2 border-b pb-1 pt-1">
		<span class="font-mono text-xs text-gray-400">
			{#key data.id}
				<Katex>{data.id}</Katex>
			{/key}
		</span>
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
		<div class="mt-1 text-center text-[10px] font-bold uppercase tracking-tighter {isClosed ? 'text-red-500' : 'text-slate-400'}">
			{#if isClosed}
				Closed
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

<style>
	/* ─── Delay countdown badge ─── */
	.delay-badge {
		position: absolute;
		top: -11px;
		right: -10px;
		display: flex;
		align-items: center;
		gap: 3px;
		padding: 2px 7px 2px 5px;
		background: #fef2f2;
		border: 1.5px solid #f87171;
		border-radius: 20px;
		font-size: 10px;
		font-weight: 700;
		color: #dc2626;
		white-space: nowrap;
		animation: delay-pulse 1.2s ease-in-out infinite;
		box-shadow: 0 0 6px rgba(239, 68, 68, 0.3);
	}

	@keyframes delay-pulse {
		0%, 100% {
			box-shadow: 0 0 4px rgba(239, 68, 68, 0.25);
			border-color: #f87171;
		}
		50% {
			box-shadow: 0 0 10px rgba(239, 68, 68, 0.55);
			border-color: #dc2626;
		}
	}
</style>
