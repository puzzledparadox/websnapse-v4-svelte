<script lang="ts">
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
	import Toast, { showToast } from '$lib/components/Toast.svelte';
	import { simulation } from '$lib/services/simulation.svelte';
	import { type GallerySystem } from '$lib/constants/gallery';
	import { onMount, untrack } from 'svelte';
	import { ShieldAlert, LayoutGrid, Maximize, Sparkles, Radiation, Download, Trash2, Layers, Focus, Copy, Hash, PanelLeftClose, PanelLeftOpen } from 'lucide-svelte';
	import dagre from 'dagre';
	import '@xyflow/svelte/dist/style.css';
	import Katex from 'svelte-katex';

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
	let sidebarOpen = $state(true);

	let contextMenuState = $state({
		show: false,
		x: 0,
		y: 0,
		options: [] as any[]
	});

	let tick = $state(0);
	let simSpeed = $state(1.5);
	let simMode = $state<'pseudorandom' | 'guided'>('pseudorandom');
	let autoPlayInterval: ReturnType<typeof setInterval> | null = null;
	let isHalted = $state(false);
	let simIsPlaying = $state(false);

	// Snapshot of initial state for restart
	let initialNodes: typeof nodes | null = null;
	let initialEdges: typeof edges | null = null;
	let initialSystemState: typeof systemState | null = null;

	// History stack for stepping back
	let simHistory = $state<any[]>([]);

	let systemState = $state({
		name: 'Binary Adder',
		div: [] as number[],  // delayed indicator vector (per-rule)
		dsv: [] as number[],  // delay status vector (per-rule)
	});

	let nodes = $state([
		{
			id: 'n1',
			type: 'neuron',
			position: { x: 150, y: 150 },
			data: { id: 'in_0', neuronType: 'input', spikes: '111', delay: 0, rules: [] }
		},
		{
			id: 'n2',
			type: 'neuron',
			position: { x: 150, y: 350 },
			data: { id: 'in_1', neuronType: 'input', spikes: '1101', delay: 0, rules: [] }
		},
		{
			id: 'n3',
			type: 'neuron',
			position: { x: 450, y: 250 },
			data: {
				id: 'add',
				neuronType: 'regular',
				spikes: 0,
				delay: 0,
				rules: ['a \\to a; 0', 'a^2/a \\to \\lambda', 'a^3/a^2 \\to a; 0']
			}
		},
		{
			id: 'n4',
			type: 'neuron',
			position: { x: 750, y: 250 },
			data: { id: 'out', neuronType: 'output', spikes: '', delay: 0, rules: [] }
		}
	]);

	let showHistory = $state(false);

	function getOrderedRules() {
		let orderedRules: string[] = [];
		nodes.forEach(n => {
			const ntype = n.data.neuronType;
			if (ntype === 'input' || ntype === 'Input' || ntype === 'output' || ntype === 'Output') return;
			const rules = n.data.rules || [];
			rules.forEach(r => orderedRules.push(`${n.data.id}: ${r}`));
		});
		return orderedRules;
	}

	function formatSpikeTrain(train: string | number) {
		if (train === undefined || train === null || train === '') return '-';
		const str = String(train);
		if (!str) return '-';
		
		let compressed = '';
		let i = 0;
		while (i < str.length) {
			let count = 1;
			while (i + 1 < str.length && str[i] === str[i + 1]) {
				count++;
				i++;
			}
			if (count > 1) {
				compressed += `${str[i]}^{${count}}`;
			} else {
				compressed += str[i];
			}
			i++;
		}
		return compressed;
	}

	function recordHistory(firedRules: string[] = []) {
		const nodeStates: Record<string, any> = {};
		nodes.forEach(n => {
			nodeStates[n.data.id] = {
				spikes: n.data.spikes,
				type: n.data.neuronType
			};
		});

		const ruleByNode: Record<string, string> = {};
		firedRules.forEach(fr => {
			const parts = fr.split(': ');
			if (parts.length >= 2) {
				const nodeId = parts[0];
				const rule = parts.slice(1).join(': ');
				ruleByNode[nodeId] = rule;
			}
		});

		simulation.history.push({
			tick: tick,
			nodeStates,
			ruleByNode
		});
	}

	let edges = $state([
		{
			id: 'e1', source: 'n1', target: 'n3', type: 'synapse',
			style: 'stroke: #a855f7; stroke-width: 2px;', data: { isFiring: false, weight: 1 },
			markerEnd: { type: MarkerType.ArrowClosed, color: '#a855f7' }
		},
		{
			id: 'e2', source: 'n2', target: 'n3', type: 'synapse',
			style: 'stroke: #a855f7; stroke-width: 2px;', data: { isFiring: false, weight: 1 },
			markerEnd: { type: MarkerType.ArrowClosed, color: '#a855f7' }
		},
		{
			id: 'e3', source: 'n3', target: 'n4', type: 'synapse',
			style: 'stroke: #a855f7; stroke-width: 2px;', data: { isFiring: false, weight: 1 },
			markerEnd: { type: MarkerType.ArrowClosed, color: '#a855f7' }
		}
	]);

	onMount(() => {
		simulation.connect();

		// Snapshot initial state for restart
		initialNodes = JSON.parse(JSON.stringify(nodes));
		initialEdges = JSON.parse(JSON.stringify(edges));
		initialSystemState = JSON.parse(JSON.stringify(systemState));

		// Listen for right-clicks on edge labels (portaled outside SVG)
		function handleEdgeLabelContext(e: Event) {
			const { edgeId, event } = (e as CustomEvent).detail;
			const edge = edges.find(ed => ed.id === edgeId);
			if (edge) {
				handleEdgeContextMenu({ edge, event });
			}
		}
		window.addEventListener('edge-label-contextmenu', handleEdgeLabelContext);
		return () => {
			window.removeEventListener('edge-label-contextmenu', handleEdgeLabelContext);
			if (autoPlayInterval) clearInterval(autoPlayInterval);
			if (previewInterval) clearInterval(previewInterval);
		};
	});

	function handleStep() {
		if (!simulation.isConnected || isHalted) return;

		// Send the full graph definition so the backend can dynamically
		// parse rules, build M_Pi, and compute stv_k for this tick.
		simulation.sendState({
			type: 'step',
			tick: tick,
			nodes: nodes.map(n => ({
				id: n.id,
				neuronType: n.data.neuronType,
				spikes: n.data.spikes,
				rules: n.data.rules || []
			})),
			edges: edges.map(e => ({
				source: e.source,
				target: e.target,
				weight: e.data?.weight ?? 1
			})),
			div: systemState.div,
			dsv: systemState.dsv
		});
	}

	function handleSimPlayPause() {
		if (autoPlayInterval) {
			// Pause
			clearInterval(autoPlayInterval);
			autoPlayInterval = null;
		} else {
			// Play — auto-step at the configured speed
			const intervalMs = Math.max(100, 1000 / simSpeed);
			autoPlayInterval = setInterval(() => {
				handleStep();
			}, intervalMs);
		}
	}

	function handleSimSpeedChange(newSpeed: number) {
		simSpeed = newSpeed;
		// If currently auto-playing, restart the interval at the new speed
		if (autoPlayInterval) {
			clearInterval(autoPlayInterval);
			const intervalMs = Math.max(100, 1000 / simSpeed);
			autoPlayInterval = setInterval(() => {
				handleStep();
			}, intervalMs);
		}
	}

	function handleSimModeChange(newMode: 'pseudorandom' | 'guided') {
		simMode = newMode;
	}

	function handleSimRestart() {
		// Stop auto-play
		if (autoPlayInterval) {
			clearInterval(autoPlayInterval);
			autoPlayInterval = null;
		}

		// Restore state to the very first recorded history frame
		if (simHistory.length > 0) {
			const firstState = simHistory[0];
			nodes = firstState.nodes;
			edges = firstState.edges;
			systemState = firstState.systemState;
			tick = firstState.tick;
			isHalted = false;
			simHistory = [];
		} else if (initialNodes && initialEdges && initialSystemState) {
			// Fallback to loaded state if no steps taken yet
			nodes = JSON.parse(JSON.stringify(initialNodes));
			edges = JSON.parse(JSON.stringify(initialEdges));
			systemState = JSON.parse(JSON.stringify(initialSystemState));
			tick = 0;
			isHalted = false;
		}

		simulation.possibilities = [];
		simulation.reset();
		recordHistory();
	}

	function handleStepBack() {
		if (simHistory.length > 0) {
			const prevState = simHistory.pop();
			nodes = prevState.nodes;
			edges = prevState.edges;
			systemState = prevState.systemState;
			tick = prevState.tick;
			isHalted = false;
			simulation.possibilities = [];
			
			if (simulation.history.length > 0) {
				simulation.history.pop();
			}
		}
	}

	function applyBranch(pos) {
		// Track which neurons fired for edge animation
		const firedNeurons = new Set<string>();
		
		const firedRules: string[] = [];
		if (pos.iv) {
			const ruleNames = getOrderedRules();
			pos.iv.forEach((fired: number, idx: number) => {
				if (fired === 1 && ruleNames[idx]) firedRules.push(ruleNames[idx]);
			});
		}

		// Save to history before modifying state
		simHistory.push({
			nodes: JSON.parse(JSON.stringify(nodes)),
			edges: JSON.parse(JSON.stringify(edges)),
			systemState: JSON.parse(JSON.stringify(systemState)),
			tick: tick
		});

		// Update nodes immutably to trigger Svelte Flow reactivity
		nodes = nodes.map((n, i) => {
			const ntype = n.data.neuronType;
			let newSpikes = n.data.spikes;

			if (ntype === 'input' || ntype === 'Input') {
				// Trim first bit from the spike train (consumed this tick)
				const train = String(n.data.spikes);
				if (train.length > 0 && train[0] === '1') {
					firedNeurons.add(n.id);
				}
				newSpikes = train.substring(1);

			} else if (ntype === 'output' || ntype === 'Output') {
				// Build the output spike train: append 0 or 1 based on received spikes
				const currentTrain = typeof n.data.spikes === 'string' ? n.data.spikes : '';
				const prevAccumulated = currentTrain.split('').filter(c => c === '1').length;
				const newAccumulated = pos.c_k[i] ?? prevAccumulated;
				const delta = newAccumulated - prevAccumulated;
				newSpikes = currentTrain + (delta > 0 ? '1' : '0');

			} else {
				// Regular neuron — update spike count
				if (pos.c_k[i] !== undefined) {
					newSpikes = pos.c_k[i];
				}
				// Neuron fired if it consumed spikes (rule_contribution < 0)
				if (pos.rule_contribution && pos.rule_contribution[i] < 0) {
					firedNeurons.add(n.id);
				}
			}

			return {
				...n,
				data: {
					...n.data,
					spikes: newSpikes,
					isFiring: firedNeurons.has(n.id)
				}
			};
		});

		// Activate firing animation on edges whose source neuron fired
		edges = edges.map(e => ({
			...e,
			data: { ...e.data, isFiring: firedNeurons.has(e.source) }
		}));

		systemState.div = pos.div;
		systemState.dsv = pos.dsv;
		tick++;
		
		recordHistory(firedRules);

		if (pos.is_halted) {
			isHalted = true;
			if (autoPlayInterval) {
				clearInterval(autoPlayInterval);
				autoPlayInterval = null;
			}
		}

		// Clear possibilities after selection
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
		isHalted = false;
		simHistory = [];
		systemState.div = [];
		systemState.dsv = [];
		simulation.possibilities = [];
		simulation.reset();
		recordHistory();
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
				isHalted = false;
				simulation.possibilities = [];

				// Rehydrate
				setTimeout(() => {
					nodes = parsed.nodes || [];
					edges = parsed.edges || [];
					tick = parsed.tick || 0;
					systemState = parsed.systemState || systemState;

					simulation.reset(); // Send Reset/Initialize command
					recordHistory();
				}, 50);
			} catch (err) {
				console.error('Failed to parse JSON', err);
			}
			// Reset file input
			event.target.value = '';
		};
		reader.readAsText(file);
	}

	function loadGallerySystem(system: GallerySystem) {
		// Stop any running simulation
		if (autoPlayInterval) {
			clearInterval(autoPlayInterval);
			autoPlayInterval = null;
		}
		simIsPlaying = false;

		// Clear canvas
		nodes = [];
		edges = [];
		tick = 0;
		isHalted = false;
		simHistory = [];
		simulation.possibilities = [];
		simulation.history = [];

		setTimeout(() => {
			// Deep-clone nodes from gallery schema
			nodes = JSON.parse(JSON.stringify(system.nodes));

			// Deep-clone edges and fix MarkerType (gallery uses plain strings)
			edges = JSON.parse(JSON.stringify(system.edges)).map((e: any) => ({
				...e,
				markerEnd: { type: MarkerType.ArrowClosed, color: '#a855f7' }
			}));

			systemState = JSON.parse(JSON.stringify(system.systemState));

			// Snapshot for restart
			initialNodes = JSON.parse(JSON.stringify(nodes));
			initialEdges = JSON.parse(JSON.stringify(edges));
			initialSystemState = JSON.parse(JSON.stringify(systemState));

			// Sync backend
			simulation.reset();
			recordHistory();

			// Auto-fit the view to show the loaded system
			setTimeout(() => fitView({ padding: 0.25, duration: 600 }), 100);

			// Toast notification
			showToast(`"${system.title}" loaded successfully`, 'success');
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

	// Auto-apply branches if deterministic (1 option) or in pseudorandom mode
	$effect(() => {
		if (simulation.possibilities && simulation.possibilities.length > 0 && !isHalted) {
			if (simMode === 'pseudorandom' || simulation.possibilities.length === 1) {
				const randomIndex = Math.floor(Math.random() * simulation.possibilities.length);
				// Use a small timeout to avoid $effect infinite loops and give UI a tick to render
				setTimeout(() => {
					if (simulation.possibilities && simulation.possibilities.length > 0) {
						applyBranch(simulation.possibilities[randomIndex]);
					}
				}, 50);
			}
		}
	});

	let previewInterval: ReturnType<typeof setInterval> | null = null;
	let previewIndex = $state(0);

	$effect(() => {
		if (simMode === 'guided' && simulation.possibilities && simulation.possibilities.length > 1 && !isHalted) {
			if (!previewInterval) {
				previewIndex = 0;
				previewInterval = setInterval(() => {
					previewIndex = (previewIndex + 1) % simulation.possibilities.length;
				}, 1500); // 1.5s interval
			}
			
			const pos = simulation.possibilities[previewIndex];
			const previewFiredNeurons = new Set<string>();
			
			// Untrack nodes and edges so modifying them doesn't trigger this effect again
			const currentNodes = untrack(() => nodes);
			const currentEdges = untrack(() => edges);

			currentNodes.forEach((n, i) => {
				const ntype = n.data.neuronType;
				if (ntype === 'input' || ntype === 'Input') {
					const train = String(n.data.spikes);
					if (train.length > 0 && train[0] === '1') {
						previewFiredNeurons.add(n.id);
					}
				} else if (ntype !== 'output' && ntype !== 'Output') {
					if (pos.rule_contribution && pos.rule_contribution[i] < 0) {
						previewFiredNeurons.add(n.id);
					}
				}
			});

			nodes = currentNodes.map(n => ({
				...n,
				data: { ...n.data, previewFiring: previewFiredNeurons.has(n.id) }
			}));

			edges = currentEdges.map(e => ({
				...e,
				data: { ...e.data, previewFiring: previewFiredNeurons.has(e.source) }
			}));

		} else {
			if (previewInterval) {
				clearInterval(previewInterval);
				previewInterval = null;
				
				const currentNodes = untrack(() => nodes);
				const currentEdges = untrack(() => edges);
				
				nodes = currentNodes.map(n => ({
					...n,
					data: { ...n.data, previewFiring: undefined }
				}));
				edges = currentEdges.map(e => ({
					...e,
					data: { ...e.data, previewFiring: undefined }
				}));
			}
		}
	});
</script>

<main class="flex h-screen w-screen overflow-hidden">
	<!-- Sidebar toggle button (always visible) -->
	{#if !sidebarOpen}
		<button
			onclick={() => sidebarOpen = true}
			class="fixed left-0 top-1/2 z-20 -translate-y-1/2 rounded-r-lg border border-l-0 border-gray-200 bg-white px-1.5 py-3 shadow-md transition-all hover:bg-purple-50 hover:shadow-lg"
			title="Open sidebar"
		>
			<PanelLeftOpen size={18} class="text-purple-600" />
		</button>
	{/if}

	<!-- String Computation Sidebar (WebSnapse 4 Everyone) -->
	<aside
		class="z-10 flex w-96 flex-col gap-4 overflow-y-auto border-r bg-white p-4 shadow-lg transition-all duration-300 ease-in-out"
		class:sidebar-open={sidebarOpen}
		class:sidebar-closed={!sidebarOpen}
	>
		<div class="flex items-center justify-between border-b pb-2">
			<button
				onclick={() => sidebarOpen = false}
				class="rounded p-1 text-gray-400 transition-colors hover:bg-gray-100 hover:text-purple-600"
				title="Hide sidebar"
			>
				<PanelLeftClose size={18} />
			</button>
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
			<GalleryPanel onSelect={loadGallerySystem} />
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
				disabled={!simulation.isConnected || isHalted}
			>
				{isHalted ? 'System Halted' : 'Step Simulation'}
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
		<Toolbar bind:activeTool={activeTool} bind:showHistory={showHistory} onClear={() => showClearModal = true} />
		<SimulationBar
			isConnected={simulation.isConnected}
			{isHalted}
			bind:isPlaying={simIsPlaying}
			onStep={handleStep}
			onStepBack={handleStepBack}
			onPlayPause={handleSimPlayPause}
			onRestart={handleSimRestart}
			onModeChange={handleSimModeChange}
			onSpeedChange={handleSimSpeedChange}
		/>

		<!-- Tick Counter HUD -->
		<div class="absolute left-4 top-4 z-50 flex items-center gap-1.5 rounded bg-gray-900/80 px-3 py-1.5 text-sm font-bold text-white shadow backdrop-blur-sm">
			<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="opacity-70"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
			Tick: {tick}
		</div>

		<!-- History Panel -->
		{#if showHistory}
			<div class="absolute right-4 top-20 z-50 flex max-h-[80vh] w-auto max-w-4xl flex-col overflow-hidden rounded-lg border border-gray-200 bg-white shadow-xl">
				<div class="flex items-center justify-between border-b bg-gray-50 px-4 py-2">
					<h3 class="font-bold text-gray-800">State History</h3>
					<button class="text-gray-500 hover:text-gray-700" onclick={() => showHistory = false}>&times;</button>
				</div>
				<div class="flex-1 overflow-auto p-4">
					{#if simulation.history.length === 0}
						<p class="text-sm text-gray-500 italic">No history yet. Start simulation or apply a branch.</p>
					{:else}
						<table class="w-full border-collapse text-center text-sm">
							<thead class="bg-gray-200">
								<tr class="text-gray-800">
									<th class="border border-gray-300 px-4 py-2 font-bold">Time</th>
									{#each nodes as node}
										<th class="border border-gray-300 px-4 py-2 font-bold">
											<Katex>{node.data.id}</Katex>
										</th>
									{/each}
								</tr>
							</thead>
							<tbody>
								{#each simulation.history as entry, i}
									<tr class={i % 2 === 0 ? 'bg-white' : 'bg-gray-100'}>
										<td class="border border-gray-300 px-4 py-2 font-bold text-gray-800">{entry.tick}</td>
										{#each nodes as node}
											<td class="border border-gray-300 px-4 py-2 text-gray-800">
												{#if node.data.neuronType === 'regular'}
													{#if entry.ruleByNode && entry.ruleByNode[node.data.id]}
														<Katex>{entry.ruleByNode[node.data.id]}</Katex>
													{:else}
														-
													{/if}
												{:else}
													{#if entry.nodeStates && entry.nodeStates[node.data.id] && String(entry.nodeStates[node.data.id].spikes) !== ''}
														<Katex>{formatSpikeTrain(entry.nodeStates[node.data.id].spikes)}</Katex>
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
			defaultEdgeOptions={{
				type: 'synapse',
				style: 'stroke: #a855f7; stroke-width: 2px;',
				data: { isFiring: false, weight: 1 },
				markerEnd: {
					type: MarkerType.ArrowClosed,
					color: '#a855f7'
				}
			}}
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
			<CustomMiniMap {nodes} {edges} />
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
		margin-left: -24rem; /* -w-96 */
		opacity: 0;
		pointer-events: none;
	}
</style>
