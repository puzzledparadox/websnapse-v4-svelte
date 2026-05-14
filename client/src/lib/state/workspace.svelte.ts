import type { Node, Edge } from '@xyflow/svelte';

export type AppNode = Node & {
	data: {
		id: string;
		neuronType: string;
		spikes: string | number;
		delay: number;
		rules?: string[];
		isFiring?: boolean;
		previewFiring?: boolean;
	}
};

export type AppEdge = Edge & {
	data?: {
		isFiring?: boolean;
		previewFiring?: boolean;
		weight?: number;
	}
};
import dagre from 'dagre';
import { MarkerType } from '@xyflow/svelte';

export class WorkspaceState {
	activeTool = $state('select');
	showHistory = $state(false);

	nodes = $state<AppNode[]>([
		{
			id: 'n1', type: 'neuron', position: { x: 150, y: 150 },
			data: { id: 'in_0', neuronType: 'input', spikes: '111', delay: 0, rules: [] }
		},
		{
			id: 'n2', type: 'neuron', position: { x: 150, y: 350 },
			data: { id: 'in_1', neuronType: 'input', spikes: '1101', delay: 0, rules: [] }
		},
		{
			id: 'n3', type: 'neuron', position: { x: 450, y: 250 },
			data: { id: 'add', neuronType: 'regular', spikes: 0, delay: 0, rules: ['a \\to a; 0', 'a^2/a \\to \\lambda', 'a^3/a^2 \\to a; 0'] }
		},
		{
			id: 'n4', type: 'neuron', position: { x: 750, y: 250 },
			data: { id: 'out', neuronType: 'output', spikes: '', delay: 0, rules: [] }
		}
	]);

	edges = $state<AppEdge[]>([
		{ id: 'e1', source: 'n1', target: 'n3', type: 'synapse', data: { isFiring: false, weight: 1 }, markerEnd: { type: MarkerType.ArrowClosed, color: 'var(--color-brand-primary)' } },
		{ id: 'e2', source: 'n2', target: 'n3', type: 'synapse', data: { isFiring: false, weight: 1 }, markerEnd: { type: MarkerType.ArrowClosed, color: 'var(--color-brand-primary)' } },
		{ id: 'e3', source: 'n3', target: 'n4', type: 'synapse', data: { isFiring: false, weight: 1 }, markerEnd: { type: MarkerType.ArrowClosed, color: 'var(--color-brand-primary)' } }
	]);

	applyAutoLayout(fitView: any) {
		const g = new dagre.graphlib.Graph();
		g.setGraph({ rankdir: 'LR', marginx: 20, marginy: 20 });
		g.setDefaultEdgeLabel(() => ({}));

		this.nodes.forEach(n => g.setNode(n.id, { width: 120, height: 80 }));
		this.edges.forEach(e => g.setEdge(e.source, e.target));

		dagre.layout(g);

		this.nodes = this.nodes.map(node => {
			const pos = g.node(node.id);
			return {
				...node,
				position: { x: pos.x - 60, y: pos.y - 40 }
			};
		});
		setTimeout(() => fitView({ padding: 0.2, duration: 800 }), 50);
	}

	applyRadialLayout(fitView: any) {
		const radius = Math.max(200, this.nodes.length * 40);
		const center = { x: 400, y: 300 };

		this.nodes = this.nodes.map((node, i) => {
			const angle = (i / this.nodes.length) * 2 * Math.PI;
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

	deleteNode(nodeId: string) {
		this.nodes = this.nodes.filter(n => n.id !== nodeId);
		this.edges = this.edges.filter(e => e.source !== nodeId && e.target !== nodeId);
	}

	deleteEdge(edgeId: string) {
		this.edges = this.edges.filter(e => e.id !== edgeId);
	}

	clear() {
		this.nodes = [];
		this.edges = [];
	}

	formatSpikeTrain(train: string | number) {
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
}

export const workspaceState = new WorkspaceState();
