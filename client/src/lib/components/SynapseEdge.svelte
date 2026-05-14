<script lang="ts">
	import { BaseEdge, getBezierPath, EdgeLabel } from '@xyflow/svelte';

	let {
		id,
		sourceX,
		sourceY,
		targetX,
		targetY,
		sourcePosition,
		targetPosition,
		markerEnd = '',
		style = '',
		data
	} = $props();

	let isFiring = $derived(data?.previewFiring !== undefined ? !!data?.previewFiring : !!data?.isFiring);

	let pathParams = $derived(
		getBezierPath({
			sourceX,
			sourceY,
			sourcePosition,
			targetX,
			targetY,
			targetPosition
		})
	);
	
	let path = $derived(pathParams[0]);
	let labelX = $derived(pathParams[1]);
	let labelY = $derived(pathParams[2]);

	let edgeStyle = $derived(
		isFiring
			? 'stroke: #a855f7; stroke-width: 2.5px;'
			: 'stroke: #334155; stroke-width: 1.5px;'
	);
</script>

<BaseEdge {path} {markerEnd} style={edgeStyle} class={isFiring ? 'synapse-firing' : ''} />

<EdgeLabel
	x={labelX}
	y={labelY}
>
	<div
		role="button"
		tabindex="0"
		class="nodrag nopan rounded px-1.5 py-0.5 text-[10px] font-bold shadow-sm border cursor-pointer
			{isFiring ? 'bg-purple-100 text-purple-800 border-purple-300' : 'bg-white text-slate-700 border-slate-200'}"
		oncontextmenu={(e) => {
			e.preventDefault();
			e.stopPropagation();
			window.dispatchEvent(new CustomEvent('edge-label-contextmenu', { detail: { edgeId: id, event: e } }));
		}}
	>
		{data?.weight ?? 1}
	</div>
</EdgeLabel>

<style>
	:global(.synapse-firing) {
		stroke-dasharray: 6 3;
		animation: marchingAnts 0.4s linear infinite;
		filter: drop-shadow(0 0 3px rgba(168, 85, 247, 0.5));
	}

	@keyframes marchingAnts {
		to {
			stroke-dashoffset: -18;
		}
	}
</style>
