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
		label = '',
		labelStyle = {},
		labelBgStyle = {},
		labelBgPadding = [0, 0],
		labelBgBorderRadius = 0,
		data = {}
	} = $props();

	// Check if this is a self-loop
	let isSelfLoop = $derived(!!data?.isSelfLoop || (sourceX === targetX && sourceY === targetY));

	// Generate path
	let pathData = $derived.by(() => {
		if (isSelfLoop) {
			// Draw a larger circular loop above the node for better clarity
			const radius = 45;
			const p = `M ${sourceX},${sourceY} 
					   C ${sourceX - radius},${sourceY - radius * 2.2} 
					     ${sourceX + radius},${sourceY - radius * 2.2} 
					     ${sourceX},${sourceY}`;
			return [p, sourceX, sourceY - radius * 1.6];
		} else {
			return getBezierPath({
				sourceX,
				sourceY,
				sourcePosition,
				targetX,
				targetY,
				targetPosition
			});
		}
	});

	let path = $derived(pathData[0]);
	let labelX = $derived(pathData[1]);
	let labelY = $derived(pathData[2]);
</script>

<BaseEdge {id} {path} {markerEnd} {style} />

{#if label}
	<EdgeLabel x={labelX} y={labelY}>
		<div class="rounded border border-purple-200 bg-white/95 px-1.5 py-0.5 text-[11px] font-mono font-medium text-purple-800 shadow-sm backdrop-blur-sm">
			{label}
		</div>
	</EdgeLabel>
{/if}
