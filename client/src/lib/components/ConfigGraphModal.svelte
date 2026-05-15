<script lang="ts">
	import { SvelteFlow, Background, Controls, MarkerType } from '@xyflow/svelte';
	import dagre from 'dagre';
	import { X, Network, Loader2 } from 'lucide-svelte';
	import ConfigGraphEdge from './ConfigGraphEdge.svelte';

	let { show = $bindable(), data } = $props<{ show: boolean, data: {nodes: any[], edges: any[], limit_reached: boolean} | null }>();

	const edgeTypes = {
		config: ConfigGraphEdge
	};

	let flowNodes = $state<any[]>([]);
	let flowEdges = $state<any[]>([]);

	$effect(() => {
		if (show && data && data.nodes && data.edges) {
			applyDagreLayout(data.nodes, data.edges);
		}
	});

	function applyDagreLayout(rawNodes: any[], rawEdges: any[]) {
		const g = new dagre.graphlib.Graph();
		g.setGraph({ rankdir: 'TB', ranksep: 100, nodesep: 80 });
		g.setDefaultEdgeLabel(() => ({}));

		rawNodes.forEach((n) => {
			g.setNode(n.id, { width: 160, height: 44 });
		});

		rawEdges.forEach((e) => {
			g.setEdge(e.source, e.target);
		});

		dagre.layout(g);

		flowNodes = rawNodes.map((n) => {
			const nodeWithPosition = g.node(n.id);
			return {
				id: n.id,
				position: {
					x: nodeWithPosition.x - 80,
					y: nodeWithPosition.y - 22
				},
				data: { label: n.label, is_halted: n.is_halted },
				type: 'default',
				style: `
					background: ${n.is_halted ? '#fff1f2' : '#ffffff'}; 
					border: 1.5px solid ${n.is_halted ? '#fda4af' : '#e9d5ff'}; 
					border-radius: 6px; 
					font-weight: 500; 
					font-family: ui-monospace, monospace; 
					padding: 10px; 
					min-width: 160px; 
					text-align: center; 
					color: #1f2937;
					font-size: 13px;
				`
			};
		});

		flowEdges = rawEdges.map((e) => {
			return {
				id: e.id,
				source: e.source,
				target: e.target,
				label: e.label,
				type: 'config',
				data: { isSelfLoop: e.source === e.target },
				markerEnd: {
					type: MarkerType.ArrowClosed,
					color: '#a855f7'
				}
			};
		});
	}
</script>

{#if show}
<div class="fixed inset-0 z-[150] flex items-center justify-center bg-gray-900/40 p-8 backdrop-blur-sm">
	<div class="flex h-full w-full flex-col overflow-hidden rounded-2xl bg-white shadow-2xl ring-1 ring-black/5">
		
		<!-- Header -->
		<div class="flex items-center justify-between border-b border-gray-100 bg-gray-50/50 px-6 py-4">
			<div class="flex items-center gap-3">
				<div class="flex h-10 w-10 items-center justify-center rounded-xl bg-purple-100 text-purple-600 shadow-inner">
					<Network size={20} />
				</div>
				<div>
					<h2 class="text-lg font-bold tracking-tight text-gray-800">Configuration Graph</h2>
					<p class="text-xs text-gray-500">State space reachability analysis</p>
				</div>
			</div>
			
			<div class="flex items-center gap-4">
				{#if data?.limit_reached}
				<div class="rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-700">
					Max States Reached
				</div>
				{/if}
				<button
					class="rounded-full p-2 text-gray-400 transition-colors hover:bg-gray-200 hover:text-gray-700"
					onclick={() => show = false}
				>
					<X size={20} />
				</button>
			</div>
		</div>

		<!-- Canvas -->
		<div class="relative flex-1 bg-gray-50">
			{#if !data}
				<div class="absolute inset-0 flex flex-col items-center justify-center text-purple-500">
					<Loader2 size={32} class="mb-4 animate-spin" />
					<p class="font-bold">Generating Graph...</p>
				</div>
			{:else}
				<SvelteFlow
					nodes={flowNodes}
					edges={flowEdges}
					{edgeTypes}
					nodesDraggable={true}
					panOnDrag={true}
					fitView
				>
					<Background bgColor="#f8fafc" />
					<Controls />
				</SvelteFlow>
			{/if}
		</div>
	</div>
</div>
{/if}
