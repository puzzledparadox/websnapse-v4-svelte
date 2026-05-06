<script lang="ts">
	import { useSvelteFlow } from '@xyflow/svelte';
	import { onMount } from 'svelte';

	let { nodes = [], edges = [] } = $props();

	const { setViewport, getViewport } = useSvelteFlow();

	// Fixed minimap dimensions
	const MAP_WIDTH = 200;
	const MAP_HEIGHT = 150;
	const PADDING = 40;
	const NODE_DEFAULT_W = 120;
	const NODE_DEFAULT_H = 80;

	// Track viewport reactively via polling (getViewport is imperative)
	let vpX = $state(0);
	let vpY = $state(0);
	let vpZoom = $state(1);
	let containerW = $state(800);
	let containerH = $state(600);
	let svgEl: SVGSVGElement | undefined = $state(undefined);

	onMount(() => {
		// Measure the container (the SvelteFlow parent)
		function measure() {
			const flowWrapper = document.querySelector('.svelte-flow');
			if (flowWrapper) {
				containerW = flowWrapper.clientWidth;
				containerH = flowWrapper.clientHeight;
			}
		}

		function tick() {
			const vp = getViewport();
			vpX = vp.x;
			vpY = vp.y;
			vpZoom = vp.zoom;
			measure();
			rafId = requestAnimationFrame(tick);
		}

		let rafId = requestAnimationFrame(tick);
		return () => cancelAnimationFrame(rafId);
	});

	// Compute the bounding box of all nodes in flow coordinates
	let bounds = $derived.by(() => {
		if (nodes.length === 0) {
			return { minX: 0, minY: 0, maxX: 600, maxY: 400 };
		}
		let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
		for (const n of nodes) {
			const w = n.measured?.width ?? NODE_DEFAULT_W;
			const h = n.measured?.height ?? NODE_DEFAULT_H;
			if (n.position.x < minX) minX = n.position.x;
			if (n.position.y < minY) minY = n.position.y;
			if (n.position.x + w > maxX) maxX = n.position.x + w;
			if (n.position.y + h > maxY) maxY = n.position.y + h;
		}
		return {
			minX: minX - PADDING,
			minY: minY - PADDING,
			maxX: maxX + PADDING,
			maxY: maxY + PADDING
		};
	});

	// Calculate uniform scale to fit everything into the minimap
	let scale = $derived.by(() => {
		const bw = bounds.maxX - bounds.minX;
		const bh = bounds.maxY - bounds.minY;
		if (bw <= 0 || bh <= 0) return 1;
		return Math.min(MAP_WIDTH / bw, MAP_HEIGHT / bh);
	});

	// Transform flow coords → minimap coords
	function toMini(x: number, y: number) {
		const bw = bounds.maxX - bounds.minX;
		const bh = bounds.maxY - bounds.minY;
		// Center the content in the minimap
		const offsetX = (MAP_WIDTH - bw * scale) / 2;
		const offsetY = (MAP_HEIGHT - bh * scale) / 2;
		return {
			x: (x - bounds.minX) * scale + offsetX,
			y: (y - bounds.minY) * scale + offsetY
		};
	}

	// Viewport rectangle (what's visible on the main canvas)
	let viewportRect = $derived.by(() => {
		// Top-left of visible area in flow coordinates
		const flowX = -vpX / vpZoom;
		const flowY = -vpY / vpZoom;
		const flowW = containerW / vpZoom;
		const flowH = containerH / vpZoom;

		const tl = toMini(flowX, flowY);
		return {
			x: tl.x,
			y: tl.y,
			width: flowW * scale,
			height: flowH * scale
		};
	});

	// Minimap node rects
	let miniNodes = $derived(
		nodes.map(n => {
			const w = n.measured?.width ?? NODE_DEFAULT_W;
			const h = n.measured?.height ?? NODE_DEFAULT_H;
			const pos = toMini(n.position.x, n.position.y);
			return {
				id: n.id,
				x: pos.x,
				y: pos.y,
				width: w * scale,
				height: h * scale,
				type: n.data?.neuronType
			};
		})
	);

	// Minimap edge lines (connect node centers)
	let miniEdges = $derived(
		edges.map(e => {
			const srcNode = nodes.find(n => n.id === e.source);
			const tgtNode = nodes.find(n => n.id === e.target);
			if (!srcNode || !tgtNode) return null;
			const sw = srcNode.measured?.width ?? NODE_DEFAULT_W;
			const sh = srcNode.measured?.height ?? NODE_DEFAULT_H;
			const tw = tgtNode.measured?.width ?? NODE_DEFAULT_W;
			const th = tgtNode.measured?.height ?? NODE_DEFAULT_H;
			// Connect from right-center of source to left-center of target
			const from = toMini(srcNode.position.x + sw, srcNode.position.y + sh / 2);
			const to = toMini(tgtNode.position.x, tgtNode.position.y + th / 2);
			return { id: e.id, x1: from.x, y1: from.y, x2: to.x, y2: to.y, isFiring: !!e.data?.isFiring };
		}).filter(Boolean)
	);

	// Drag handling — click/drag the minimap to pan
	let isDragging = $state(false);

	function panToMiniCoord(clientX: number, clientY: number) {
		if (!svgEl) return;
		const rect = svgEl.getBoundingClientRect();
		const mx = clientX - rect.left;
		const my = clientY - rect.top;

		// Convert minimap coords back to flow coords
		const bw = bounds.maxX - bounds.minX;
		const bh = bounds.maxY - bounds.minY;
		const offsetX = (MAP_WIDTH - bw * scale) / 2;
		const offsetY = (MAP_HEIGHT - bh * scale) / 2;

		const flowX = (mx - offsetX) / scale + bounds.minX;
		const flowY = (my - offsetY) / scale + bounds.minY;

		// Center the viewport at the clicked flow position
		setViewport({
			x: -(flowX - containerW / vpZoom / 2) * vpZoom,
			y: -(flowY - containerH / vpZoom / 2) * vpZoom,
			zoom: vpZoom
		});
	}

	function handlePointerDown(e: PointerEvent) {
		isDragging = true;
		(e.currentTarget as SVGSVGElement).setPointerCapture(e.pointerId);
		panToMiniCoord(e.clientX, e.clientY);
	}

	function handlePointerMove(e: PointerEvent) {
		if (!isDragging) return;
		panToMiniCoord(e.clientX, e.clientY);
	}

	function handlePointerUp() {
		isDragging = false;
	}
</script>

<div class="custom-minimap" class:dragging={isDragging}>
	<svg
		bind:this={svgEl}
		width={MAP_WIDTH}
		height={MAP_HEIGHT}
		viewBox="0 0 {MAP_WIDTH} {MAP_HEIGHT}"
		onpointerdown={handlePointerDown}
		onpointermove={handlePointerMove}
		onpointerup={handlePointerUp}
		onpointerleave={handlePointerUp}
	>
		<!-- Background -->
		<rect x="0" y="0" width={MAP_WIDTH} height={MAP_HEIGHT} fill="#faf5ff" rx="6" />

		<!-- Edges -->
		{#each miniEdges as edge}
			{#if edge}
				<line
					x1={edge.x1}
					y1={edge.y1}
					x2={edge.x2}
					y2={edge.y2}
					stroke={edge.isFiring ? '#a855f7' : '#94a3b8'}
					stroke-width={edge.isFiring ? 1.5 : 1}
					opacity={edge.isFiring ? 1 : 0.6}
				/>
				<!-- Arrowhead dot -->
				<circle cx={edge.x2} cy={edge.y2} r="1.5" fill={edge.isFiring ? '#a855f7' : '#94a3b8'} />
			{/if}
		{/each}

		<!-- Nodes -->
		{#each miniNodes as mn}
			<rect
				x={mn.x}
				y={mn.y}
				width={mn.width}
				height={mn.height}
				rx="2"
				fill={mn.type === 'input' ? '#a7f3d0' : mn.type === 'output' ? '#fde68a' : '#e9d5ff'}
				stroke={mn.type === 'input' ? '#059669' : mn.type === 'output' ? '#d97706' : '#7c3aed'}
				stroke-width="1"
			/>
		{/each}

		<!-- Viewport indicator -->
		<rect
			x={viewportRect.x}
			y={viewportRect.y}
			width={viewportRect.width}
			height={viewportRect.height}
			fill="none"
			stroke="#7c3aed"
			stroke-width="1.5"
			rx="2"
			opacity="0.9"
		/>
	</svg>
</div>

<style>
	.custom-minimap {
		position: absolute;
		bottom: 12px;
		right: 12px;
		z-index: 50;
		border-radius: 8px;
		border: 1px solid #e2e8f0;
		box-shadow:
			0 4px 12px rgba(0, 0, 0, 0.08),
			0 0 0 1px rgba(124, 58, 237, 0.1);
		overflow: hidden;
		cursor: grab;
		background: white;
		transition: box-shadow 0.2s;
	}

	.custom-minimap:hover {
		box-shadow:
			0 6px 20px rgba(0, 0, 0, 0.12),
			0 0 0 1px rgba(124, 58, 237, 0.2);
	}

	.custom-minimap.dragging {
		cursor: grabbing;
		box-shadow:
			0 8px 24px rgba(124, 58, 237, 0.2),
			0 0 0 2px rgba(124, 58, 237, 0.3);
	}

	.custom-minimap svg {
		display: block;
	}
</style>
