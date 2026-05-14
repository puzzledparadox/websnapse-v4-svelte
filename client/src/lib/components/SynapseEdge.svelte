<!--
	@component
	SynapseEdge.svelte
	
	A custom Svelte Flow edge component representing an SN P system synapse.
	Renders a bezier curve with an edge label showing the synaptic weight.
	When the `isFiring` prop is true, it displays an animated marching-ants 
	stroke to visualize spike propagation.
-->
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
		data = undefined
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

</script>

<BaseEdge {path} {markerEnd} class={isFiring ? 'synapse-edge-firing' : 'synapse-edge-idle'} />

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

