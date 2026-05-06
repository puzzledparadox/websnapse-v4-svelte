<script lang="ts">
	import { SvelteFlow, Background, Controls, MarkerType, useSvelteFlow, type Node, type Edge } from '@xyflow/svelte';
	import { PanOnScrollMode } from '@xyflow/system';
	import NeuronNode from '$lib/components/NeuronNode.svelte';
	import SynapseEdge from '$lib/components/SynapseEdge.svelte';
	import Toolbar from '$lib/components/Toolbar.svelte';
	import NodeCreationModal from '$lib/components/NodeCreationModal.svelte';
	import ContextMenu from '$lib/components/ContextMenu.svelte';
	import { simulation } from '$lib/services/simulation.svelte';
	import { onMount } from 'svelte';
	import { ShieldAlert, LayoutGrid, Maximize, Sparkles, Radiation, Download, Trash2, Layers, Focus, Copy, Hash } from 'lucide-svelte';
	import dagre from 'dagre';
	import '@xyflow/svelte/dist/style.css';

	const nodeTypes = {
		neuron: NeuronNode
	};

	const edgeTypes = {
		synapse: SynapseEdge
	};

	// Svelte 5 Runes for reactive state
	let activeTool = $state('select');
	const { screenToFlowPosition, fitView, setCenter } = useSvelteFlow();

	let showNodeModal = $state(false);
	let pendingNodePosition = $state({ x: 0, y: 0 });
	let defaultNodeId = $state('');
	let editTargetNode = $state<Node | null>(null);

	let showClearModal = $state(false);

	let contextMenuState = $state({
		show: false,
		x: 0,
		y: 0,
		options: [] as any[]
	});

	let tick = $state(0);
	let systemState = $state({
		name: 'Fibonacci Generator',
		m_pi: [
			[-1, 1, 1],
			[-2, 0, 0]
		],
		stv_k: [0, 0, 0],
		rule_delays: [1, 0],
		div: [0, 0],
		dsv: [0, 0],
		st_next: [1, 1, 1]
	});

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
			type: 'synapse',
			style: 'stroke: #a855f7; stroke-width: 2px;',
			data: { isFiring: true },
			markerEnd: {
				type: MarkerType.ArrowClosed,
				color: '#a855f7'
			}
		},
		{
			id: 'e1-3',
			source: 'n1',
			target: 'n3',
			type: 'synapse',
			style: 'stroke: #a855f7; stroke-width: 2px;',
			data: { isFiring: false },
			markerEnd: {
				type: MarkerType.ArrowClosed,
				color: '#a855f7'
			}
		}
	]);

	onMount(() => {
		simulation.connect();

		// Listen for right-clicks on edge labels (portaled outside SVG)
		function handleEdgeLabelContext(e: Event) {
			const { edgeId, event } = (e as CustomEvent).detail;
			const edge = edges.find(ed => ed.id === edgeId);
			if (edge) {
				handleEdgeContextMenu({ edge, event });
			}
		}
		window.addEventListener('edge-label-contextmenu', handleEdgeLabelContext);
		return () => window.removeEventListener('edge-label-contextmenu', handleEdgeLabelContext);
	});

	function handleStep() {
		simulation.sendState({
			tick: tick,
			state: {
				c_k: nodes.map((n) => n.data.spikes),
				div: systemState.div,
				dsv: systemState.dsv,
				st_next: systemState.st_next
			},
			m_pi: systemState.m_pi,
			stv_k: systemState.stv_k,
			rule_delays: systemState.rule_delays,
			rules: []
		});
	}

	function applyBranch(pos) {
		for (let i = 0; i < nodes.length; i++) {
			if (pos.c_k[i] !== undefined) {
				nodes[i].data.spikes = pos.c_k[i];
			}
		}
		systemState.div = pos.div;
		systemState.dsv = pos.dsv;
		tick++;

		// Clear possibilities after selection to represent moving to the next step
		simulation.possibilities = [];
	}

	function handlePaneClick({ event }: { event: MouseEvent | TouchEvent }) {
		if (activeTool === 'node') {
			pendingNodePosition = screenToFlowPosition({
				x: event.clientX,
				y: event.clientY
			});
			defaultNodeId = Math.random().toString(36).substring(2, 7);
			editTargetNode = null;
			showNodeModal = true;
		}
	}

	function applyAutoLayout() {
		const g = new dagre.graphlib.Graph();
		g.setGraph({ rankdir: 'LR', marginx: 20, marginy: 20 });
		g.setDefaultEdgeLabel(() => ({}));

		nodes.forEach(n => g.setNode(n.id, { width: 120, height: 80 }));
		edges.forEach(e => g.setEdge(e.source, e.target));

		dagre.layout(g);

		nodes = nodes.map(node => {
			const pos = g.node(node.id);
			return {
				...node,
				position: { x: pos.x - 60, y: pos.y - 40 }
			};
		});
		setTimeout(() => fitView({ padding: 0.2, duration: 800 }), 50);
	}

	function applyRadialLayout() {
		const radius = Math.max(200, nodes.length * 40);
		const center = { x: 400, y: 300 };

		nodes = nodes.map((node, i) => {
			const angle = (i / nodes.length) * 2 * Math.PI;
			return {
				...node,
				position: {
					x: center.x + radius * Math.cos(angle) - 60,
					y: center.y + radius * Math.sin(angle) - 40
				}
			};
		});
		setTimeout(() => fitView({ padding: 0.2, duration: 800 }), 50);
	}

	function handlePaneContextMenu({ event }: { event: MouseEvent }) {
		event.preventDefault();
		event.stopPropagation();
		contextMenuState = {
			show: true,
			x: event.clientX,
			y: event.clientY,
			options: [
				{ label: 'New Node', icon: LayoutGrid, action: () => {
					pendingNodePosition = screenToFlowPosition({ x: event.clientX, y: event.clientY });
					defaultNodeId = Math.random().toString(36).substring(2, 7);
					editTargetNode = null;
					showNodeModal = true;
				}},
				{ label: 'Fit View', icon: Maximize, action: () => fitView({ padding: 0.2, duration: 800 }) },
				{ label: 'Auto layout', icon: Sparkles, action: applyAutoLayout },
				{ label: 'Radial layout', icon: Radiation, action: applyRadialLayout },
				{ divider: true },
				{ label: 'Save', icon: Download, action: exportSystem },
				{ label: 'Clear', icon: Trash2, action: () => showClearModal = true }
			]
		};
	}

	function handleNodeContextMenu({ node, event }: { node: Node, event: MouseEvent }) {
		event.preventDefault();
		event.stopPropagation();
		contextMenuState = {
			show: true,
			x: event.clientX,
			y: event.clientY,
			options: [
				{ label: 'Edit node', icon: Layers, action: () => {
					editTargetNode = node;
					showNodeModal = true;
				}},
				{ label: 'Focus node', icon: Focus, action: () => {
					setCenter(node.position.x + 60, node.position.y + 40, { zoom: 1.5, duration: 800 });
				}},
				{ label: 'Duplicate', icon: Copy, action: () => {
					const newId = `n-${Date.now()}`;
					nodes = [...nodes, {
						...node,
						id: newId,
						position: { x: node.position.x + 50, y: node.position.y + 50 },
						data: { ...node.data, id: Math.random().toString(36).substring(2, 7) }
					}];
				}},
				{ divider: true },
				{ label: 'Delete', icon: Trash2, action: () => {
					nodes = nodes.filter(n => n.id !== node.id);
					edges = edges.filter(e => e.source !== node.id && e.target !== node.id);
				}}
			]
		};
	}

	function handleEdgeContextMenu({ edge, event }: { edge: Edge, event: MouseEvent }) {
		event.preventDefault();
		event.stopPropagation();
		contextMenuState = {
			show: true,
			x: event.clientX,
			y: event.clientY,
			options: [
				{ label: 'Edit weight', icon: Hash, action: () => {
					const w = window.prompt('Enter new weight:', String(edge.data?.weight ?? 1));
					if (w !== null) {
						const parsed = parseInt(w, 10);
						if (!isNaN(parsed)) {
							edges = edges.map(e => e.id === edge.id ? { ...e, data: { ...e.data, weight: parsed } } : e);
						}
					}
				}},
				{ divider: true },
				{ label: 'Delete', icon: Trash2, action: () => {
					edges = edges.filter(e => e.id !== edge.id);
				}}
			]
		};
	}

	function createPendingNode(data: { id: string, type: string, spikes: number | string, rules: string[], isEdit?: boolean }) {
		if (data.isEdit && editTargetNode) {
			nodes = nodes.map(n => n.id === editTargetNode.id ? {
				...n,
				data: {
					...n.data,
					id: data.id,
					neuronType: data.type,
					spikes: data.spikes,
					rules: data.rules
				}
			} : n);
		} else {
			const newId = `n-${Date.now()}`;
			nodes = [...nodes, {
				id: newId,
				type: 'neuron',
				position: pendingNodePosition,
				data: {
					id: data.id,
					neuronType: data.type,
					spikes: data.spikes,
					delay: 0,
					rules: data.rules
				}
			}];
		}
		editTargetNode = null;
	}

	function handleNodeClick({ node, event }: { node: Node, event: MouseEvent | TouchEvent }) {
		if (activeTool === 'delete') {
			nodes = nodes.filter(n => n.id !== node.id);
			edges = edges.filter(e => e.source !== node.id && e.target !== node.id);
		}
	}

	function handleEdgeClick({ edge, event }: { edge: Edge, event: MouseEvent | TouchEvent }) {
		if (activeTool === 'delete') {
			edges = edges.filter(e => e.id !== edge.id);
		}
	}

	function handleClear() {
		nodes = [];
		edges = [];
		tick = 0;
		systemState.m_pi = [];
		systemState.stv_k = [];
		systemState.rule_delays = [];
		systemState.div = [];
		systemState.dsv = [];
		systemState.st_next = [];
		simulation.possibilities = [];
		simulation.reset();
	}

	function exportSystem() {
		const dataStr =
			'data:text/json;charset=utf-8,' +
			encodeURIComponent(
				JSON.stringify({
					nodes: nodes,
					edges: edges,
					tick: tick,
					systemState: systemState
				})
			);
		const downloadAnchorNode = document.createElement('a');
		downloadAnchorNode.setAttribute('href', dataStr);
		downloadAnchorNode.setAttribute('download', (systemState.name || 'system') + '.json');
		document.body.appendChild(downloadAnchorNode);
		downloadAnchorNode.click();
		downloadAnchorNode.remove();
	}

	let fileInput;

	function importSystem(event) {
		const file = event.target.files[0];
		if (!file) return;

		const reader = new FileReader();
		reader.onload = (e) => {
			try {
				const parsed = JSON.parse(e.target.result);
				// Clear canvas and reset tick
				nodes = [];
				edges = [];
				tick = 0;
				simulation.possibilities = [];

				// Rehydrate
				setTimeout(() => {
					nodes = parsed.nodes || [];
					edges = parsed.edges || [];
					tick = parsed.tick || 0;
					systemState = parsed.systemState || systemState;

					simulation.reset(); // Send Reset/Initialize command
				}, 50);
			} catch (err) {
				console.error('Failed to parse JSON', err);
			}
			// Reset file input
			event.target.value = '';
		};
		reader.readAsText(file);
	}

	function loadTemplate(type) {
		nodes = [];
		edges = [];
		tick = 0;
		simulation.possibilities = [];

		setTimeout(() => {
			if (type === 'parity') {
				nodes = [
					{
						id: 'n1',
						type: 'neuron',
						position: { x: 250, y: 250 },
						data: { id: 'σ₁', neuronType: 'input', spikes: 0, delay: 0, rules: ['a^2/a \\to a; 1'] }
					}
				];
				edges = [];
				systemState = {
					name: 'Even Parity Checker',
					m_pi: [[-2]],
					stv_k: [0],
					rule_delays: [0],
					div: [0],
					dsv: [0],
					st_next: [1]
				};
			} else if (type === 'fibonacci') {
				nodes = [
					{
						id: 'n1',
						type: 'neuron',
						position: { x: 150, y: 250 },
						data: {
							id: 'σ₁',
							neuronType: 'input',
							spikes: 2,
							delay: 0,
							rules: ['a^2/a \\to a; 1', 'a \\to \\lambda']
						}
					},
					{
						id: 'n2',
						type: 'neuron',
						position: { x: 500, y: 150 },
						data: { id: 'σ₂', neuronType: 'output', spikes: 1, delay: 0, rules: [] }
					},
					{
						id: 'n3',
						type: 'neuron',
						position: { x: 500, y: 350 },
						data: { id: 'σ₃', neuronType: 'output', spikes: 3, delay: 0, rules: [] }
					}
				];
				edges = [
					{
						id: 'e1-2',
						source: 'n1',
						target: 'n2',
						type: 'synapse',
						style: 'stroke: #a855f7; stroke-width: 2px;',
						data: { isFiring: true },
						markerEnd: { type: MarkerType.ArrowClosed, color: '#a855f7' }
					},
					{
						id: 'e1-3',
						source: 'n1',
						target: 'n3',
						type: 'synapse',
						style: 'stroke: #a855f7; stroke-width: 2px;',
						data: { isFiring: false },
						markerEnd: { type: MarkerType.ArrowClosed, color: '#a855f7' }
					}
				];
				systemState = {
					name: 'Fibonacci Generator',
					m_pi: [
						[-1, 1, 1],
						[-2, 0, 0]
					],
					stv_k: [0, 0, 0],
					rule_delays: [1, 0],
					div: [0, 0],
					dsv: [0, 0],
					st_next: [1, 1, 1]
				};
			}
			simulation.reset();
		}, 50);
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
				m_pi: [[-2, 0, 0]],
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
	<aside class="z-10 flex w-96 flex-col gap-4 overflow-y-auto border-r bg-white p-4 shadow-lg">
		<div class="flex items-center justify-between border-b pb-2">
			<h2 class="text-xl font-bold text-gray-800">String Judge</h2>
			<div class="flex items-center gap-2">
				<div
					class="h-3 w-3 rounded-full {simulation.isConnected ? 'bg-green-500' : 'bg-red-500'}"
				></div>
				<span class="text-xs font-medium text-gray-600"
					>{simulation.isConnected ? 'Online' : 'Offline'}</span
				>
			</div>
		</div>

		<!-- Persistence & Gallery -->
		<div class="mb-4 border-b pb-4">
			<h3 class="mb-2 text-sm font-semibold text-gray-700">System Persistence</h3>
			<div class="mb-2 flex gap-2">
				<button
					onclick={exportSystem}
					class="flex-1 rounded border border-blue-600 px-2 py-1 text-xs font-semibold text-blue-600 transition-colors hover:bg-blue-50"
				>
					Export System
				</button>
				<button
					onclick={() => fileInput.click()}
					class="flex-1 rounded border border-green-600 px-2 py-1 text-xs font-semibold text-green-600 transition-colors hover:bg-green-50"
				>
					Import System
				</button>
				<input
					type="file"
					bind:this={fileInput}
					accept=".json"
					onchange={importSystem}
					class="hidden"
				/>
			</div>

			<h3 class="mt-4 mb-2 text-sm font-semibold text-gray-700">Pre-built Gallery</h3>
			<div class="flex gap-2">
				<button
					onclick={() => loadTemplate('parity')}
					class="flex-1 rounded bg-gray-100 px-2 py-1 text-xs font-medium text-gray-700 hover:bg-gray-200"
				>
					Even Parity
				</button>
				<button
					onclick={() => loadTemplate('fibonacci')}
					class="flex-1 rounded bg-gray-100 px-2 py-1 text-xs font-medium text-gray-700 hover:bg-gray-200"
				>
					Fibonacci
				</button>
			</div>
		</div>

		<!-- Max Search Depth -->
		<div class="flex flex-col gap-1">
			<label for="maxDepth" class="text-sm font-semibold text-gray-700"
				>Max Search Depth (ticks)</label
			>
			<input
				id="maxDepth"
				type="number"
				bind:value={timeLimit}
				class="rounded border border-gray-300 p-2 text-sm focus:border-purple-500 focus:ring-1 focus:ring-purple-500 focus:outline-none"
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
								<div class="flex w-20 items-center justify-center">
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
		<div class="mt-2 border-t pt-4">
			<h3 class="mb-2 text-sm font-semibold text-gray-700">Manual Simulation</h3>
			<button
				onclick={handleStep}
				class="w-full rounded bg-gray-800 p-2 text-sm font-semibold text-white hover:bg-gray-900 disabled:opacity-50"
				disabled={!simulation.isConnected}
			>
				Step Simulation
			</button>
			{#if simulation.possibilities && simulation.possibilities.length > 0}
				<div class="mt-4 flex max-h-40 flex-col gap-2 overflow-y-auto">
					<h3 class="text-xs font-bold text-gray-700">Next State Branches:</h3>
					{#each simulation.possibilities as pos, i}
						<button
							onclick={() => applyBranch(pos)}
							class="rounded border bg-white p-2 text-left text-xs shadow-sm transition-colors hover:border-purple-500 hover:bg-purple-50"
						>
							<div class="font-bold text-purple-700">Branch {i + 1}</div>
							<div>
								<span class="font-semibold text-gray-600">Spikes:</span> [{pos.c_k.join(', ')}]
							</div>
							<div>
								<span class="font-semibold text-gray-600">Delay Status:</span> [{pos.dsv.join(
									', '
								)}]
							</div>
						</button>
					{/each}
				</div>
			{/if}
		</div>
	</aside>

	<!-- Visualization Canvas (WebSnapse Reloaded) -->
	<section class="relative flex-1">
		<Toolbar bind:activeTool={activeTool} onClear={() => showClearModal = true} />
		<NodeCreationModal
			bind:show={showNodeModal}
			defaultId={defaultNodeId}
			initialNode={editTargetNode}
			onSubmit={createPendingNode}
		/>
		<ContextMenu
			bind:show={contextMenuState.show}
			x={contextMenuState.x}
			y={contextMenuState.y}
			options={contextMenuState.options}
			onClose={() => contextMenuState.show = false}
		/>

		<!-- Clear Confirmation Modal -->
		{#if showClearModal}
			<div class="absolute inset-0 z-[100] flex items-center justify-center bg-black/20 backdrop-blur-sm">
				<div class="w-80 rounded-lg border border-red-200 bg-white p-6 shadow-xl">
					<h3 class="mb-2 flex items-center gap-2 text-lg font-bold text-red-600">
						<ShieldAlert size={24} />
						Clear Canvas?
					</h3>
					<p class="mb-6 text-sm text-gray-600">
						This will permanently delete all nodes and edges. The simulation tick will be reset to 0. This action cannot be undone.
					</p>
					<div class="flex justify-end gap-2">
						<button
							class="rounded border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100"
							onclick={() => showClearModal = false}
						>
							Cancel
						</button>
						<button
							class="rounded bg-red-600 px-4 py-2 text-sm font-bold text-white hover:bg-red-700"
							onclick={() => {
								handleClear();
								showClearModal = false;
							}}
						>
							Yes, Nuke It
						</button>
					</div>
				</div>
			</div>
		{/if}

		<SvelteFlow
			bind:nodes={nodes}
			bind:edges={edges}
			{nodeTypes}
			{edgeTypes}
			nodesDraggable={activeTool === 'select' || activeTool === 'node'}
			nodesConnectable={activeTool === 'edge'}
			panOnDrag={activeTool === 'hand'}
			selectionOnDrag={activeTool === 'select'}
			elementsSelectable={activeTool === 'select' || activeTool === 'delete'}
			panOnScrollMode={PanOnScrollMode.Free}
			onpaneclick={handlePaneClick}
			onnodeclick={handleNodeClick}
			onedgeclick={handleEdgeClick}
			onpanecontextmenu={handlePaneContextMenu}
			onnodecontextmenu={handleNodeContextMenu}
			onedgecontextmenu={handleEdgeContextMenu}
		>
			<Background />
			<Controls />
		</SvelteFlow>
	</section>
</main>
