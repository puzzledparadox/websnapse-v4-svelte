<!--
	@component
	+page.svelte
	
	The main application workspace for WebSnapse v4.
	Orchestrates the Svelte Flow canvas, simulation state, WebSockets communication,
	and layout management. It coordinates between the visual graph representation
	and the mathematical matrix engine in the Python backend.
-->
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
	import BranchModal from '$lib/components/BranchModal.svelte';
	import Toast, { showToast } from '$lib/components/Toast.svelte';
	import { simulation } from '$lib/services/simulation.svelte';
	import { type GallerySystem } from '$lib/constants/gallery';
	import { onMount } from 'svelte';
	import { 
		ShieldAlert, LayoutGrid, Maximize, Sparkles, Radiation, Download, 
		Trash2, Layers, Focus, Copy, Hash, PanelLeftClose, PanelLeftOpen,
		Database, Zap, Settings2, Table2, Info, Upload
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
	let activeTool = $state('select');
	const { screenToFlowPosition, fitView, setCenter } = useSvelteFlow();

	let showNodeModal = $state(false);
	let pendingNodePosition = $state({ x: 0, y: 0 });
	let defaultNodeId = $state('');
	let editTargetNode = $state<Node | null>(null);

	let showClearModal = $state(false);
	let sidebarOpen = $state(true);
	let sidebarWidth = $state(384);
	let isResizingSidebar = $state(false);

	let openSections = $state({
		persistence: true,
		gallery: true,
		config: true,
		judging: true
	});

	let galleryHeight = $state(300);

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

	/**
	 * Converts the per-rule `dsv` (Delay Status Vector) and `div` (Delayed Indicator Vector)
	 * received from the backend into a per-node delay map for UI rendering.
	 * 
	 * A node is considered "closed" if ANY of its rules has `div[r] == 1` 
	 * (actively counting down OR about to fire).
	 * 
	 * @param dsv - Delay Status Vector.
	 * @param div - Delayed Indicator Vector.
	 * @returns A Map mapping `nodeId` -> `maxDelayValue`.
	 */
	function buildNodeDelayMap(dsv: number[], div: number[]): Map<string, number> {
		const delayMap = new Map<string, number>();
		let ruleIdx = 0;
		nodes.forEach(n => {
			const ntype = n.data.neuronType;
			if (ntype === 'input' || ntype === 'Input' || ntype === 'output' || ntype === 'Output') return;
			const ruleCount = (n.data.rules || []).length;
			let maxDelay = 0;
			for (let r = 0; r < ruleCount; r++) {
				const globalR = ruleIdx + r;
				if (div[globalR] === 1) {
					maxDelay = Math.max(maxDelay, dsv[globalR]);
				}
			}
			delayMap.set(n.id, maxDelay);
			ruleIdx += ruleCount;
		});
		return delayMap;
	}

	/**
	 * Formats a raw spike train string into a condensed LaTeX representation.
	 * Examples: "11100" -> "1^{3}\ 0^{2}".
	 * 
	 * @param train - Raw spike string or number.
	 * @returns Condensed LaTeX string.
	 */
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

	/**
	 * Captures a snapshot of the current canvas state and adds it to the
	 * global `simulation.history` array for the State History table.
	 * 
	 * @param firedRules - An array of rule strings that fired to produce this state.
	 */
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

		recordHistory();

		function handleMouseMove(e: MouseEvent) {
			if (isResizingSidebar) {
				sidebarWidth = Math.max(280, Math.min(600, e.clientX));
			}
		}

		function handleMouseUp() {
			isResizingSidebar = false;
			document.body.style.cursor = '';
			document.body.style.userSelect = 'auto';
		}

		window.addEventListener('mousemove', handleMouseMove);
		window.addEventListener('mouseup', handleMouseUp);

		return () => {
			window.removeEventListener('edge-label-contextmenu', handleEdgeLabelContext);
			window.removeEventListener('mousemove', handleMouseMove);
			window.removeEventListener('mouseup', handleMouseUp);
			if (autoPlayInterval) clearInterval(autoPlayInterval);
		};
	});

	/**
	 * Triggers a single simulation step.
	 * Packages the visual graph topology and delay vectors into a JSON payload
	 * and sends it to the backend engine to calculate the next state(s).
	 */
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
				// Also clear rules for the state we stepped back into
				if (simulation.history.length > 0) {
					simulation.history[simulation.history.length - 1].ruleByNode = {};
				}
			}
		}
	}

	/**
	 * Applies a selected non-deterministic branch possibility to the visual canvas.
	 * This updates node spike counts, delay countdowns, and triggers synapse animations.
	 * 
	 * @param pos - The specific possibility state returned by the engine.
	 */
	function applyBranch(pos) {
		// Track which neurons fired for edge animation
		const firedNeurons = new Set<string>();
		
		const firedRules: string[] = [];
		const ruleNames = getOrderedRules();
		const dv = pos.dv || [];
		const iv = pos.iv || [];

		// Record rules that are either SELECTED (dv) or FIRING (iv)
		// This ensures delayed rules show up in history both when triggered and when they finish.
		dv.forEach((selected: number, idx: number) => {
			if (selected === 1 && ruleNames[idx]) {
				firedRules.push(ruleNames[idx]);
			}
		});

		iv.forEach((fired: number, idx: number) => {
			if (fired === 1 && ruleNames[idx]) {
				// Avoid duplicates if a rule is both selected and firing (e.g. delay 0)
				if (!firedRules.includes(ruleNames[idx])) {
					firedRules.push(ruleNames[idx]);
				}
			}
		});

		// Save to history before modifying state
		simHistory.push({
			nodes: JSON.parse(JSON.stringify(nodes)),
			edges: JSON.parse(JSON.stringify(edges)),
			systemState: JSON.parse(JSON.stringify(systemState)),
			tick: tick
		});

		// Build per-node delay map from backend's per-rule dsv/div vectors.
		const nodeDelayMap = buildNodeDelayMap(pos.dsv || [], pos.div || []);

		// Build the set of node IDs that are CLOSED after this tick.
		// Closed = delay > 0 (a delayed rule is still counting down).
		// A closed neuron cannot send OR receive spikes, so its outgoing and
		// incoming synapses must not animate.
		const closedNodeIds = new Set<string>();
		nodeDelayMap.forEach((delay, id) => { if (delay > 0) closedNodeIds.add(id); });

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

			// Visual firing logic:
			// • A neuron is only considered "firing" (purple glow) when it actually
			//   produces output (iv=1) and is no longer closed.
			// • If a neuron is closed (delay > 0), it shows the red glow and countdown badge.
			const newDelay = nodeDelayMap.get(n.id) ?? 0;

			return {
				...n,
				data: {
					...n.data,
					spikes: newSpikes,
					delay: newDelay,
					isFiring: !closedNodeIds.has(n.id) && firedNeurons.has(n.id)
				}
			};
		});

		// Activate firing animation on edges only when:
		//   • the source neuron actually fired (is in firedNeurons), AND
		//   • the source is not closed (cannot send), AND
		//   • the target is not closed (cannot receive)
		edges = edges.map(e => ({
			...e,
			data: {
				...e.data,
				isFiring:
					firedNeurons.has(e.source) &&
					!closedNodeIds.has(e.source) &&
					!closedNodeIds.has(e.target)
			}
		}));

		systemState.div = pos.div;
		systemState.dsv = pos.dsv;

		// 1. Update the rules for the CURRENT tick (the one we are transitioning from)
		if (simulation.history.length > 0) {
			const lastEntry = simulation.history[simulation.history.length - 1];
			const ruleByNode: Record<string, string> = {};
			firedRules.forEach((fr) => {
				const parts = fr.split(': ');
				if (parts.length >= 2) {
					const nodeId = parts[0];
					const rule = parts.slice(1).join(': ');
					ruleByNode[nodeId] = rule;
				}
			});
			lastEntry.ruleByNode = ruleByNode;
		}

		// 2. Transition to the next tick
		tick++;

		// 3. Record the NEW state with no rules picked yet
		recordHistory([]);

		if (pos.is_halted) {
			isHalted = true;
			if (autoPlayInterval) {
				clearInterval(autoPlayInterval);
				autoPlayInterval = null;
			}
			showToast('Simulation halted', 'info');
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

	/**
	 * Automatically layouts the graph from left-to-right using Dagre.
	 */
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
		class="z-10 flex flex-col overflow-hidden border-r bg-white shadow-lg transition-[margin,opacity] duration-300 ease-in-out"
		class:sidebar-open={sidebarOpen}
		class:sidebar-closed={!sidebarOpen}
		style="width: {sidebarWidth}px; min-width: {sidebarWidth}px;"
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
				onclick={() => sidebarOpen = false}
				class="rounded-md p-1.5 text-gray-400 transition-colors hover:bg-gray-200 hover:text-gray-700"
				title="Hide sidebar"
			>
				<PanelLeftClose size={18} />
			</button>
		</div>

		<!-- Sidebar Content (Scrollable) -->
		<div class="flex-1 overflow-y-auto overflow-x-hidden custom-scrollbar">
			<!-- Persistence & Gallery -->
			<SidebarSection title="System Storage" icon={Database} bind:isOpen={openSections.persistence}>
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

			<SidebarSection title="Pre-built Gallery" icon={Zap} bind:isOpen={openSections.gallery} bind:height={galleryHeight}>
				<div class="pt-2">
					<GalleryPanel onSelect={loadGallerySystem} />
				</div>
			</SidebarSection>

			<!-- Judging Configuration -->
			<SidebarSection title="Judgement Config" icon={Settings2} bind:isOpen={openSections.config}>
				<div class="flex flex-col gap-3 pt-2">
					<div class="flex flex-col gap-1.5">
						<div class="flex items-center justify-between">
							<label for="maxDepth" class="text-[11px] font-bold text-gray-600 uppercase tracking-tight"
								>Max Search Depth</label
							>
							<span class="rounded bg-purple-100 px-1.5 py-0.5 text-[10px] font-bold text-purple-700">{timeLimit} ticks</span>
						</div>
						<input
							id="maxDepth"
							type="range"
							bind:value={timeLimit}
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
			<SidebarSection title="String Judgement" icon={Table2} bind:isOpen={openSections.judging} fill={true}>
				<div class="flex flex-col gap-3 pt-2">
					{#if testStrings.length === 0}
						<div class="flex flex-col items-center justify-center rounded-xl border border-dashed border-gray-200 py-8 text-center">
							<div class="mb-2 text-gray-300">
								<Table2 size={32} />
							</div>
							<p class="px-4 text-[11px] text-gray-400">No bitstrings added to the test suite yet.</p>
						</div>
					{:else}
						<div class="flex flex-col gap-2">
							{#each testStrings as testString, i}
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
										onclick={() => removeString(i)}
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
							onclick={addString}
							class="flex w-full items-center justify-center gap-2 rounded-xl border border-purple-200 py-2.5 text-xs font-bold text-purple-600 transition-all hover:bg-purple-50 hover:border-purple-300"
						>
							<span class="text-lg leading-none">+</span> Add New String
						</button>
						<button
							onclick={handleJudge}
							class="flex w-full items-center justify-center gap-2 rounded-xl bg-purple-600 py-2.5 text-xs font-bold text-white shadow-md shadow-purple-200 transition-all hover:bg-purple-700 hover:shadow-lg active:scale-[0.98]"
						>
							<Zap size={14} fill="currentColor" />
							Judge All Strings
						</button>
					</div>
				</div>
			</SidebarSection>
		</div>

		<!-- Resize Handle -->
		<div 
			class="absolute right-0 top-0 h-full w-1 cursor-col-resize transition-colors hover:bg-purple-400/30"
			onmousedown={(e) => {
				isResizingSidebar = true;
				document.body.style.cursor = 'col-resize';
				document.body.style.userSelect = 'none';
			}}
		></div>
	</aside>

	<!-- Visualization Canvas (WebSnapse Reloaded) -->
	<section class="relative flex-1">
		<Toolbar bind:activeTool={activeTool} bind:showHistory={showHistory} onClear={() => showClearModal = true} />
		<!-- Non-Deterministic Branch Selection Modal (Guided Mode only) -->
		{#if simMode === 'guided' && !isHalted}
			<BranchModal
				possibilities={simulation.possibilities}
				{nodes}
				{tick}
				onSelect={(pos) => applyBranch(pos)}
			/>
		{/if}
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
