<!--
	@component
	+page.svelte
	
	The main application workspace for WebSnapse v4.
	Orchestrates the Svelte Flow canvas, simulation state, WebSockets communication,
	and layout management. It coordinates between the visual graph representation
	and the mathematical matrix engine in the Python backend.
-->
<script lang="ts">
	import { env } from '$env/dynamic/public';
	import { uiState } from '$lib/state/ui.svelte';
	import { workspaceState } from '$lib/state/workspace.svelte';
	import { judgementState } from '$lib/state/judgement.svelte';
	import { SvelteFlow, Background, Controls, MarkerType, useSvelteFlow, type Node, type Edge } from '@xyflow/svelte';
	import CustomMiniMap from '$lib/components/CustomMiniMap.svelte';
	import { PanOnScrollMode } from '@xyflow/system';
	import NeuronNode from '$lib/components/NeuronNode.svelte';
	import SynapseEdge from '$lib/components/SynapseEdge.svelte';
	import Toolbar from '$lib/components/Toolbar.svelte';
	import SimulationBar from '$lib/components/SimulationBar.svelte';
	import NodeCreationModal from '$lib/components/NodeCreationModal.svelte';
	import ContextMenu from '$lib/components/ContextMenu.svelte';
	import GalleryPanel from '$lib/components/GalleryPanel.svelte';
	import BranchModal from '$lib/components/BranchModal.svelte';
	import ConfigGraphModal from '$lib/components/ConfigGraphModal.svelte';
	import Toast, { showToast } from '$lib/components/Toast.svelte';
	import { simulation } from '$lib/services/simulation.svelte';
	import { benchmark } from '$lib/services/benchmark.svelte';
	import { type GallerySystem } from '$lib/constants/gallery';
	import { onMount, tick } from 'svelte';
	import { 
		ShieldAlert, LayoutGrid, Maximize, Sparkles, Radiation, Download, 
		Trash2, Layers, Focus, Copy, Hash, PanelLeftClose, PanelLeftOpen,
		Database, Zap, Settings2, Table2, Info, Upload, Network
	} from 'lucide-svelte';
	import dagre from 'dagre';
	import '@xyflow/svelte/dist/style.css';
	import Katex from 'svelte-katex';
	import SidebarSection from '$lib/components/SidebarSection.svelte';

	const nodeTypes = {
		neuron: NeuronNode
	};

	const edgeTypes = {
		synapse: SynapseEdge
	};

	// Svelte 5 Runes for reactive state
	const { screenToFlowPosition, fitView, setCenter } = useSvelteFlow();

	let configGraphData = $state<{nodes: any[], edges: any[], limit_reached: boolean} | null>(null);
	let isGeneratingGraph = $state(false);
	let maxStates = $state(500);

	async function generateConfigGraph() {
		uiState.showConfigGraphModal = true;
		configGraphData = null;
		isGeneratingGraph = true;

		try {
			const apiUrl = env.PUBLIC_API_URL || 'http://127.0.0.1:8000';
			const res = await fetch(`${apiUrl}/api/config-graph`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					nodes: workspaceState.nodes.map(n => ({ 
						...n.data, 
						id: n.id, 
						userLabel: n.data.id 
					})),
					edges: workspaceState.edges,
					max_states: maxStates
				})
			});
			if (!res.ok) {
				const errorText = await res.text();
				console.error('Config graph error:', res.status, errorText);
				throw new Error(`Failed to generate graph: ${res.status}`);
			}
			configGraphData = await res.json();
		} catch (e) {
			console.error('Fetch error:', e);
			showToast('Failed to generate configuration graph', 'error');
			uiState.showConfigGraphModal = false;
		} finally {
			isGeneratingGraph = false;
		}
	}

	onMount(() => {
		simulation.connect();
		simulation.snapshotInitialState();

		// Listen for right-clicks on edge labels (portaled outside SVG)
		function handleEdgeLabelContext(e: Event) {
			const { edgeId, event } = (e as CustomEvent).detail;
			const edge = workspaceState.edges.find(ed => ed.id === edgeId);
			if (edge) {
				handleEdgeContextMenu({ edge, event });
			}
		}
		window.addEventListener('edge-label-contextmenu', handleEdgeLabelContext);

		function handleMouseMove(e: MouseEvent) {
			if (uiState.isResizingSidebar) {
				uiState.sidebarWidth = Math.max(280, Math.min(600, e.clientX));
			}
		}

		function handleMouseUp() {
			uiState.isResizingSidebar = false;
			document.body.style.cursor = '';
			document.body.style.userSelect = 'auto';
		}

		window.addEventListener('mousemove', handleMouseMove);
		window.addEventListener('mouseup', handleMouseUp);

		return () => {
			window.removeEventListener('edge-label-contextmenu', handleEdgeLabelContext);
			window.removeEventListener('mousemove', handleMouseMove);
			window.removeEventListener('mouseup', handleMouseUp);
		};
	});

	function handlePaneClick({ event }: { event: any }) {
		if (workspaceState.activeTool === 'node') {
			uiState.pendingNodePosition = screenToFlowPosition({
				x: event.clientX,
				y: event.clientY
			});
			uiState.defaultNodeId = Math.random().toString(36).substring(2, 7);
			uiState.editTargetNode = null;
			uiState.showNodeModal = true;
		}
	}

	/**
	 * Automatically layouts the graph from left-to-right using Dagre.
	 */
	function handlePaneContextMenu({ event }: { event: MouseEvent }) {
		event.preventDefault();
		event.stopPropagation();
		uiState.contextMenuState = {
			show: true,
			x: event.clientX,
			y: event.clientY,
			options: [
				{ label: 'New Node', icon: LayoutGrid, action: () => {
					uiState.pendingNodePosition = screenToFlowPosition({ x: event.clientX, y: event.clientY });
					uiState.defaultNodeId = Math.random().toString(36).substring(2, 7);
					uiState.editTargetNode = null;
					uiState.showNodeModal = true;
				}},
				{ label: 'Fit View', icon: Maximize, action: () => fitView({ padding: 0.2, duration: 800 }) },
				{ label: 'Auto layout', icon: Sparkles, action: ( ) => workspaceState.applyAutoLayout(fitView) },
				{ label: 'Radial layout', icon: Radiation, action: ( ) => workspaceState.applyRadialLayout(fitView) },
				{ divider: true },
				{ label: 'Save', icon: Download, action: exportSystem },
				{ label: 'Clear', icon: Trash2, action: () => uiState.showClearModal = true }
			]
		};
	}

	function handleNodeContextMenu({ node, event }: { node: Node, event: MouseEvent }) {
		event.preventDefault();
		event.stopPropagation();
		uiState.contextMenuState = {
			show: true,
			x: event.clientX,
			y: event.clientY,
			options: [
				{ label: 'Edit node', icon: Layers, action: () => {
					uiState.editTargetNode = node as any;
					uiState.showNodeModal = true;
				}},
				{ label: 'Focus node', icon: Focus, action: () => {
					setCenter(node.position.x + 60, node.position.y + 40, { zoom: 1.5, duration: 800 });
				}},
				{ label: 'Duplicate', icon: Copy, action: () => {
					const newId = `n-${Date.now()}`;
					workspaceState.nodes = [...workspaceState.nodes, {
						...node,
						id: newId,
						position: { x: node.position.x + 50, y: node.position.y + 50 },
						data: { ...node.data, id: Math.random().toString(36).substring(2, 7) }
					} as any];
				}},
				{ divider: true },
				{ label: 'Delete', icon: Trash2, action: () => {
					workspaceState.nodes = workspaceState.nodes.filter(n => n.id !== node.id);
					workspaceState.edges = workspaceState.edges.filter(e => e.source !== node.id && e.target !== node.id);
				}}
			]
		};
	}

	function handleEdgeContextMenu({ edge, event }: { edge: Edge, event: MouseEvent }) {
		event.preventDefault();
		event.stopPropagation();
		uiState.contextMenuState = {
			show: true,
			x: event.clientX,
			y: event.clientY,
			options: [
				{ label: 'Edit weight', icon: Hash, action: () => {
					const w = window.prompt('Enter new weight:', String(edge.data?.weight ?? 1));
					if (w !== null) {
						const parsed = parseInt(w, 10);
						if (!isNaN(parsed)) {
							workspaceState.edges = workspaceState.edges.map(e => e.id === edge.id ? { ...e, data: { ...e.data, weight: parsed } } : e);
						}
					}
				}},
				{ divider: true },
				{ label: 'Delete', icon: Trash2, action: () => {
					workspaceState.edges = workspaceState.edges.filter(e => e.id !== edge.id);
				}}
			]
		};
	}

	function createPendingNode(data: { id: string, type: string, spikes: number | string, rules: string[], isEdit?: boolean }) {
		const editNode = uiState.editTargetNode;
		if (data.isEdit && editNode) {
			if (data.id !== editNode.data.id) {
				simulation.renameNodeInHistory(editNode.data.id, data.id);
			}
			workspaceState.nodes = workspaceState.nodes.map(n => n.id === editNode.id ? {
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
			workspaceState.nodes = [...workspaceState.nodes, {
				id: newId,
				type: 'neuron',
				position: uiState.pendingNodePosition,
				data: {
					id: data.id,
					neuronType: data.type,
					spikes: data.spikes,
					delay: 0,
					rules: data.rules
				}
			}];
		}
		uiState.editTargetNode = null;
	}

	function handleNodeClick({ node, event }: { node: Node, event: MouseEvent | TouchEvent }) {
		if (workspaceState.activeTool === 'delete') {
			workspaceState.nodes = workspaceState.nodes.filter(n => n.id !== node.id);
			workspaceState.edges = workspaceState.edges.filter(e => e.source !== node.id && e.target !== node.id);
		}
	}

	function handleEdgeClick({ edge, event }: { edge: Edge, event: MouseEvent | TouchEvent }) {
		if (workspaceState.activeTool === 'delete') {
			workspaceState.edges = workspaceState.edges.filter(e => e.id !== edge.id);
		}
	}

	function handleClear() {
		workspaceState.clear();
		simulation.snapshotInitialState();
		simulation.restart();
	}

	function exportSystem() {
		const dataStr =
			'data:text/json;charset=utf-8,' +
			encodeURIComponent(
				JSON.stringify({
					nodes: workspaceState.nodes,
					edges: workspaceState.edges,
					tick: simulation.tick,
					systemState: simulation.systemState
				})
			);
		const downloadAnchorNode = document.createElement('a');
		downloadAnchorNode.setAttribute('href', dataStr);
		downloadAnchorNode.setAttribute('download', (simulation.systemState.name || 'system') + '.json');
		document.body.appendChild(downloadAnchorNode);
		downloadAnchorNode.click();
		downloadAnchorNode.remove();
	}

	let fileInput: HTMLInputElement;

	function importSystem(event: any) {
		const file = event.target.files[0];
		if (!file) return;

		const reader = new FileReader();
		reader.onload = (e) => {
			if (e.target) {
				try {
					const parsed = JSON.parse(e.target.result as string);
					benchmark.startLoad();
					workspaceState.clear();
					simulation.tick = 0;
					simulation.isHalted = false;
					simulation.possibilities = [];

					// Rehydrate
					setTimeout(async () => {
						workspaceState.nodes = parsed.nodes || [];
						workspaceState.edges = parsed.edges || [];
						simulation.tick = parsed.tick || 0;
						simulation.systemState = parsed.systemState || simulation.systemState;

						simulation.snapshotInitialState();
						simulation.restart(); // Send Reset/Initialize command
						setTimeout(() => fitView({ padding: 0.25, duration: 600 }), 100);
						await tick();
						benchmark.endLoad();
						showToast('System imported successfully', 'success');
					}, 50);
				} catch (err) {
					console.error('Failed to parse JSON', err);
					showToast('Failed to parse JSON file', 'error');
				}
			}
			event.target.value = '';
		};
		reader.readAsText(file);
	}

	async function loadGallerySystem(system: GallerySystem) {
		benchmark.startLoad();
		simulation.pause();
		workspaceState.clear();
		simulation.tick = 0;
		simulation.isHalted = false;
		simulation.possibilities = [];
		simulation.history = [];

		setTimeout(async () => {
			workspaceState.nodes = JSON.parse(JSON.stringify(system.nodes));
			workspaceState.edges = JSON.parse(JSON.stringify(system.edges)).map((e: any) => ({
				...e,
				markerEnd: { type: MarkerType.ArrowClosed, color: '#a855f7' }
			}));

			simulation.systemState = JSON.parse(JSON.stringify(system.systemState));
			simulation.snapshotInitialState();
			simulation.restart();
			setTimeout(() => fitView({ padding: 0.25, duration: 600 }), 100);
			await tick();
			benchmark.endLoad();
			showToast(`"${system.title}" loaded successfully`, 'success');
		}, 50);
	}

	$effect(() => { judgementState.syncResults(); });

	</script>

<main class="flex h-screen w-screen overflow-hidden">
	<!-- Sidebar toggle button (always visible) -->
	{#if !uiState.sidebarOpen}
		<button
			onclick={() => uiState.sidebarOpen = true}
			class="fixed left-0 top-1/2 z-20 -translate-y-1/2 rounded-r-lg border border-l-0 border-gray-200 bg-white px-1.5 py-3 shadow-md transition-all hover:bg-purple-50 hover:shadow-lg"
			title="Open sidebar"
		>
			<PanelLeftOpen size={18} class="text-purple-600" />
		</button>
	{/if}

	<!-- String Computation Sidebar (WebSnapse 4 Everyone) -->
	<aside
		class="z-10 flex flex-col overflow-hidden border-r bg-white shadow-lg transition-[margin,opacity] duration-300 ease-in-out"
		class:sidebar-open={uiState.sidebarOpen}
		class:sidebar-closed={!uiState.sidebarOpen}
		style="width: {uiState.sidebarWidth}px; min-width: {uiState.sidebarWidth}px;"
	>
		<!-- Sidebar Header -->
		<div class="flex items-center justify-between border-b bg-gray-50/50 px-4 py-3">
			<div class="flex items-center gap-3">
				<div class="flex h-8 w-8 items-center justify-center rounded-lg bg-purple-600 text-white shadow-sm">
					<Layers size={18} />
				</div>
				<div>
					<h2 class="text-sm font-bold text-gray-800">WebSnapse Workspace</h2>
					<div class="flex items-center gap-1.5">
						<div
							class="h-2 w-2 rounded-full {simulation.isConnected ? 'bg-green-500' : 'bg-red-500'}"
						></div>
						<span class="text-[10px] font-medium text-gray-500 uppercase tracking-wider"
							>{simulation.isConnected ? 'Online' : 'Offline'}</span
						>
					</div>
				</div>
			</div>
			<button
				onclick={() => uiState.sidebarOpen = false}
				class="rounded-md p-1.5 text-gray-400 transition-colors hover:bg-gray-200 hover:text-gray-700"
				title="Hide sidebar"
			>
				<PanelLeftClose size={18} />
			</button>
		</div>

		<!-- Sidebar Content (Scrollable) -->
		<div class="flex-1 overflow-y-auto overflow-x-hidden custom-scrollbar">
			<!-- Persistence & Gallery -->
			<SidebarSection title="System Storage" icon={Database} bind:isOpen={uiState.openSections.persistence}>
				<div class="flex flex-col gap-3 pt-2">
					<div class="flex gap-2">
						<button
							onclick={exportSystem}
							class="flex flex-1 items-center justify-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50/50 px-2 py-2 text-[11px] font-bold text-blue-700 transition-all hover:bg-blue-100 active:scale-[0.98]"
						>
							<Download size={14} />
							Export
						</button>
						<button
							onclick={() => fileInput.click()}
							class="flex flex-1 items-center justify-center gap-1.5 rounded-lg border border-emerald-200 bg-emerald-50/50 px-2 py-2 text-[11px] font-bold text-emerald-700 transition-all hover:bg-emerald-100 active:scale-[0.98]"
						>
							<Upload size={14} />
							Import
						</button>
						<input
							type="file"
							bind:this={fileInput}
							accept=".json"
							onchange={importSystem}
							class="hidden"
						/>
					</div>
				</div>
			</SidebarSection>

			<SidebarSection title="Pre-built Gallery" icon={Zap} bind:isOpen={uiState.openSections.gallery} bind:height={uiState.galleryHeight}>
				<div class="pt-2">
					<GalleryPanel onSelect={loadGallerySystem} />
				</div>
			</SidebarSection>

			<!-- Judging Configuration -->
			<SidebarSection title="Judgement Config" icon={Settings2} bind:isOpen={uiState.openSections.config}>
				<div class="flex flex-col gap-3 pt-2">
					<div class="flex flex-col gap-1.5">
						<div class="flex items-center justify-between">
							<label for="maxDepth" class="text-[11px] font-bold text-gray-600 uppercase tracking-tight"
								>Max Search Depth</label
							>
							<span class="rounded bg-purple-100 px-1.5 py-0.5 text-[10px] font-bold text-purple-700">{judgementState.timeLimit} ticks</span>
						</div>
						<input
							id="maxDepth"
							type="range"
							bind:value={judgementState.timeLimit}
							min="1"
							max="500"
							step="10"
							class="h-1.5 w-full cursor-pointer appearance-none rounded-lg bg-gray-200 accent-purple-600"
						/>
						<p class="text-[10px] text-gray-400 italic">Maximum simulation ticks to explore before rejection.</p>
					</div>
				</div>
			</SidebarSection>

			<!-- Test Strings Table -->
			<SidebarSection title="String Judgement" icon={Table2} bind:isOpen={uiState.openSections.judging} fill={true}>
				<div class="flex flex-col gap-3 pt-2">
					{#if judgementState.testStrings.length === 0}
						<div class="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 py-8 text-center">
							<div class="mb-2 text-gray-300">
								<Table2 size={32} />
							</div>
							<p class="px-4 text-[11px] text-gray-400">No bitstrings added to the test suite yet.</p>
						</div>
					{:else}
						<div class="flex flex-col gap-2">
							{#each judgementState.testStrings as testString, i}
								<div class="group relative flex items-center gap-2 rounded-xl border border-gray-100 bg-gray-50/50 p-2 transition-all hover:border-purple-200 hover:bg-white hover:shadow-sm">
									<input
										type="text"
										bind:value={testString.value}
										placeholder="e.g. 1010"
										class="min-w-0 flex-1 bg-transparent px-2 py-1 text-xs font-medium text-gray-700 focus:outline-none"
									/>
									<div class="flex w-16 items-center justify-center">
										{#if testString.status === 'idle'}
											<span class="rounded-full bg-gray-100 px-2 py-0.5 text-[9px] font-bold text-gray-400 uppercase tracking-wider">Idle</span>
										{:else if testString.status === 'judging'}
											<span class="flex items-center gap-1 text-[9px] font-bold text-blue-500 uppercase tracking-wider">
												<div class="h-1 w-1 animate-pulse rounded-full bg-blue-500"></div>
												Judging
											</span>
										{:else if testString.status === 'accepted'}
											<span class="rounded-full bg-green-100 px-2 py-0.5 text-[9px] font-bold text-green-600 uppercase tracking-wider">Accepted</span>
										{:else if testString.status === 'rejected'}
											<span class="rounded-full bg-red-100 px-2 py-0.5 text-[9px] font-bold text-red-600 uppercase tracking-wider">Rejected</span>
										{/if}
									</div>
									<button
										onclick={() => judgementState.removeString(i)}
										class="flex h-5 w-5 items-center justify-center rounded-full bg-gray-200 text-gray-500 transition-colors hover:bg-red-100 hover:text-red-600 active:scale-90"
										title="Remove"
									>
										&times;
									</button>
								</div>
							{/each}
						</div>
					{/if}
					
					<div class="mt-2 flex flex-col gap-2">
						<button
							onclick={judgementState.addString}
							class="flex w-full items-center justify-center gap-2 rounded-xl border border-purple-200 py-2.5 text-xs font-bold text-purple-600 transition-all hover:bg-purple-50 hover:border-purple-300"
						>
							<span class="text-lg leading-none">+</span> Add New String
						</button>
						<button
							onclick={judgementState.handleJudge}
							class="flex w-full items-center justify-center gap-2 rounded-xl bg-purple-600 py-2.5 text-xs font-bold text-white shadow-md shadow-purple-200 transition-all hover:bg-purple-700 hover:shadow-lg active:scale-[0.98]"
						>
							<Zap size={14} fill="currentColor" />
							Judge All Strings
						</button>
					</div>
				</div>
			</SidebarSection>

			<!-- Configuration Graph Section -->
			<SidebarSection title="Configuration Graph" icon={Network} bind:isOpen={uiState.openSections.configGraph}>
				<div class="flex flex-col gap-3 pt-2">
					<div class="flex flex-col gap-1.5">
						<div class="flex items-center justify-between">
							<label for="maxStates" class="text-[11px] font-bold tracking-tight text-gray-600 uppercase">Max States</label>
							<span class="rounded bg-purple-100 px-1.5 py-0.5 text-[10px] font-bold text-purple-700">{maxStates}</span>
						</div>
						<input
							id="maxStates"
							type="range"
							bind:value={maxStates}
							min="10"
							max="1000"
							step="10"
							class="h-1.5 w-full cursor-pointer appearance-none rounded-lg bg-gray-200 accent-purple-600"
						/>
						<p class="text-[10px] italic text-gray-400">Limit reachability state space to prevent crashes.</p>
					</div>
					<button
						onclick={generateConfigGraph}
						disabled={isGeneratingGraph}
						class="flex w-full items-center justify-center gap-2 rounded-xl bg-purple-600 py-2.5 text-xs font-bold text-white shadow-md shadow-purple-200 transition-all hover:bg-purple-700 hover:shadow-lg active:scale-[0.98] disabled:opacity-50"
					>
						<Network size={14} fill="currentColor" />
						Generate Graph
					</button>
				</div>
			</SidebarSection>
		</div>

		<!-- Resize Handle -->
		<div 
			class="absolute right-0 top-0 h-full w-1 cursor-col-resize transition-colors hover:bg-purple-400/30"
			onmousedown={(e) => {
				uiState.isResizingSidebar = true;
				document.body.style.cursor = 'col-resize';
				document.body.style.userSelect = 'none';
			}}
		></div>
	</aside>

	<!-- Visualization Canvas (WebSnapse Reloaded) -->
	<section class="relative flex-1">
		<Toolbar bind:activeTool={workspaceState.activeTool} bind:showHistory={workspaceState.showHistory} onClear={() => uiState.showClearModal = true} />
		<!-- Non-Deterministic Branch Selection Modal (Guided Mode only) -->
		{#if simulation.mode === 'guided' && !simulation.isHalted}
			<BranchModal
				possibilities={simulation.possibilities}
				nodes={workspaceState.nodes}
				tick={simulation.tick}
				onSelect={(pos) => simulation.applyBranch(pos)}
			/>
		{/if}
		<SimulationBar
			isConnected={simulation.isConnected}
			bind:isPlaying={simulation.isPlaying}
			onStep={() => simulation.handleStep()}
			onStepBack={() => simulation.stepBack()}
			onPlayPause={() => simulation.togglePlayPause()}
			onRestart={() => simulation.restart()}
			onModeChange={(m: 'pseudorandom' | 'guided' | 'random') => simulation.mode = m}
			onSpeedChange={(s: number) => simulation.setSpeed(s)}
		/>

		<!-- Tick Counter HUD -->
		<div class="absolute left-4 top-4 z-50 flex items-center gap-1.5 rounded bg-gray-900/80 px-3 py-1.5 text-sm font-bold text-white shadow backdrop-blur-sm">
			<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="opacity-70"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
			Tick: {simulation.tick}
		</div>

		<!-- History Panel -->
		{#if workspaceState.showHistory}
			<div class="absolute right-4 top-20 z-50 flex max-h-[80vh] w-auto max-w-4xl flex-col overflow-hidden rounded-lg border border-gray-200 bg-white shadow-xl">
				<div class="flex items-center justify-between border-b bg-gray-50 px-4 py-2">
					<h3 class="font-bold text-gray-800">State History</h3>
					<button class="text-gray-500 hover:text-gray-700" onclick={() => workspaceState.showHistory = false}>&times;</button>
				</div>
				<div class="flex-1 overflow-auto p-4">
					{#if simulation.history.length === 0}
						<p class="text-sm text-gray-500 italic">No history yet. Start simulation or apply a branch.</p>
					{:else}
						<table class="w-full border-collapse text-center text-sm">
							<thead class="bg-gray-200">
								<tr class="text-gray-800">
									<th class="border border-gray-300 px-4 py-2 font-bold">Time</th>
									{#each workspaceState.nodes as node}
										<th class="border border-gray-300 px-4 py-2 font-bold">
											{#key node.data.id}
												<Katex>{node.data.id}</Katex>
											{/key}
										</th>
									{/each}
								</tr>
							</thead>
							<tbody>
								{#each simulation.history as entry, i}
									<tr class={i % 2 === 0 ? 'bg-white' : 'bg-gray-100'}>
										<td class="border border-gray-300 px-4 py-2 font-bold text-gray-800">{entry.tick}</td>
										{#each workspaceState.nodes as node}
											<td class="border border-gray-300 px-4 py-2 text-gray-800">
												{#if node.data.neuronType === 'regular'}
													{#if entry.ruleByNode && entry.ruleByNode[node.data.id]}
														<Katex>{entry.ruleByNode[node.data.id]}</Katex>
													{:else}
														-
													{/if}
												{:else}
													{#if entry.nodeStates && entry.nodeStates[node.data.id] && String(entry.nodeStates[node.data.id].spikes) !== ''}
														<Katex>{workspaceState.formatSpikeTrain(entry.nodeStates[node.data.id].spikes)}</Katex>
													{:else}
														-
													{/if}
												{/if}
											</td>
										{/each}
									</tr>
								{/each}
							</tbody>
						</table>
					{/if}
				</div>
			</div>
		{/if}

		<NodeCreationModal
			bind:show={uiState.showNodeModal}
			onCancel={() => uiState.showNodeModal = false}
			defaultId={uiState.defaultNodeId}
			initialNode={uiState.editTargetNode}
			onSubmit={createPendingNode}
		/>
		<ContextMenu
			show={uiState.contextMenuState.show}
			x={uiState.contextMenuState.x}
			y={uiState.contextMenuState.y}
			options={uiState.contextMenuState.options}
			onClose={() => uiState.contextMenuState.show = false}
		/>

		<!-- Clear Confirmation Modal -->
		{#if uiState.showClearModal}
			<div class="absolute inset-0 z-[100] flex items-center justify-center bg-black/20 backdrop-blur-sm">
				<div class="w-80 rounded-lg border border-red-200 bg-white p-6 shadow-xl">
					<h3 class="mb-2 flex items-center gap-2 text-lg font-bold text-red-600">
						<ShieldAlert size={24} />
						Clear Canvas?
					</h3>
					<p class="mb-6 text-sm text-gray-600">
						This will permanently delete all workspaceState.nodes and workspaceState.edges. The simulation simulation.tick will be reset to 0. This action cannot be undone.
					</p>
					<div class="flex justify-end gap-2">
						<button
							class="rounded border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100"
							onclick={() => uiState.showClearModal = false}
						>
							Cancel
						</button>
						<button
							class="rounded bg-red-600 px-4 py-2 text-sm font-bold text-white hover:bg-red-700"
							onclick={() => {
								handleClear();
								uiState.showClearModal = false;
							}}
						>
							Yes, Nuke It
						</button>
					</div>
				</div>
			</div>
		{/if}

		<!-- Config Graph Modal -->
		<ConfigGraphModal bind:show={uiState.showConfigGraphModal} data={configGraphData} />

		<SvelteFlow
			bind:nodes={workspaceState.nodes}
			bind:edges={workspaceState.edges}
			{nodeTypes}
			{edgeTypes}
			defaultEdgeOptions={{
				type: 'synapse',
				data: { isFiring: false, weight: 1 },
				markerEnd: {
					type: MarkerType.ArrowClosed,
					color: 'var(--color-brand-primary)'
				}
			}}
			nodesDraggable={workspaceState.activeTool === 'select' || workspaceState.activeTool === 'node'}
			nodesConnectable={workspaceState.activeTool === 'edge'}
			panOnDrag={workspaceState.activeTool === 'hand'}
			selectionOnDrag={workspaceState.activeTool === 'select'}
			elementsSelectable={workspaceState.activeTool === 'select' || workspaceState.activeTool === 'delete'}
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
			<CustomMiniMap nodes={workspaceState.nodes} edges={workspaceState.edges} />
		</SvelteFlow>
	</section>

	<!-- Toast notifications -->
	<Toast />
</main>

<style>
	.sidebar-open {
		margin-left: 0;
		opacity: 1;
	}

	.sidebar-closed {
		margin-left: -600px; /* Use a large enough value for transition */
		opacity: 0;
		pointer-events: none;
	}

	.custom-scrollbar::-webkit-scrollbar {
		width: 4px;
	}
	.custom-scrollbar::-webkit-scrollbar-track {
		background: transparent;
	}
	.custom-scrollbar::-webkit-scrollbar-thumb {
		background: #e5e7eb;
		border-radius: 10px;
	}
	.custom-scrollbar::-webkit-scrollbar-thumb:hover {
		background: #d1d5db;
	}

	/* Fix for handles cursor lag/inversion */
	:global(.svelte-flow__handle) {
		cursor: crosshair !important;
		transition: none !important;
	}
</style>
