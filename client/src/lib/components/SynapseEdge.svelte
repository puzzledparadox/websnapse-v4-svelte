<script lang="ts">
	import { BaseEdge, getBezierPath } from '@xyflow/svelte';

	let {
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
</script>

<BaseEdge {path} {markerEnd} {style} />

{#if data?.isFiring}
	<circle r="4" fill="#a855f7" style="filter: drop-shadow(0 0 4px #a855f7);">
		<animateMotion dur="1s" repeatCount="indefinite" {path} />
	</circle>
{/if}
