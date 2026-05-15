/**
 * Pre-built SN P System Gallery
 * 
 * Each system is a complete schema that can be loaded directly into the
 * WebSnapse v4 canvas. Nodes/edges follow the same structure used by
 * +page.svelte state, and rules use LaTeX notation for svelte-katex rendering.
 */

/**
 * Interface defining the structure of a pre-built SN P system in the gallery.
 */
export interface GallerySystem {
	id: string;
	title: string;
	description: string;
	category: 'generators' | 'arithmetic' | 'comparators' | 'string-languages' | 'stress-tests' | 'custom';
	nodes: any[];
	edges: any[];
	systemState: {
		name: string;
		div: number[];
		dsv: number[];
	};
}

/**
 * Shared helper function to construct standard synapse edges for gallery systems.
 * 
 * @param id - The unique identifier for the edge.
 * @param source - The ID of the source neuron.
 * @param target - The ID of the target neuron.
 * @param weight - The synaptic weight (default is 1).
 * @returns A formatted Svelte Flow edge object.
 */
function makeEdge(
	id: string,
	source: string,
	target: string,
	weight: number = 1
) {
	return {
		id,
		source,
		target,
		type: 'synapse',
		style: 'stroke: #a855f7; stroke-width: 2px;',
		data: { isFiring: false, weight },
		markerEnd: { type: 'arrowclosed', color: '#a855f7' }
	};
}

// ─── 2N Generator ──────────────────────────────────────────────────────────────
// A three-neuron system that generates a spike train encoding 2n.
// Neuron 1 (σ₁): 2 spikes, rules: a²/a → a; 1, a → λ
// Neuron 2 (σ₂): 1 spike,  rules: a → a; 1, a → a; 2
// Neuron 3 (σ₃): 3 spikes, rules: a³ → a; 0, a → a; 2, a² → λ
// Output environment (env_out)
// ────────────────────────────────────────────────────────────────────────────────
const twoNGenerator: GallerySystem = {
	id: '2n-generator',
	title: '2N Generator',
	description: 'Generates a spike train representing 2n. Uses three regular neurons with forgetting rules to produce the sequence.',
	category: 'generators',
	nodes: [
		{
			id: 'n1',
			type: 'neuron',
			position: { x: 100, y: 150 },
			data: {
				id: '\\sigma_1',
				neuronType: 'regular',
				spikes: 2,
				delay: 0,
				rules: ['a^2/a \\to a; 1', 'a \\to \\lambda']
			}
		},
		{
			id: 'n2',
			type: 'neuron',
			position: { x: 400, y: 300 },
			data: {
				id: '\\sigma_2',
				neuronType: 'regular',
				spikes: 1,
				delay: 0,
				rules: ['a \\to a; 1', 'a \\to a; 2']
			}
		},
		{
			id: 'n3',
			type: 'neuron',
			position: { x: 600, y: 100 },
			data: {
				id: '\\sigma_3',
				neuronType: 'regular',
				spikes: 3,
				delay: 0,
				rules: ['a^3 \\to a; 0', 'a \\to a; 2', 'a^2 \\to \\lambda']
			}
		},
		{
			id: 'n4',
			type: 'neuron',
			position: { x: 900, y: 200 },
			data: {
				id: 'env_{out}',
				neuronType: 'output',
				spikes: '',
				delay: 0,
				rules: []
			}
		}
	],
	edges: [
		makeEdge('e1-2', 'n1', 'n2'),  // σ₁ → σ₂
		makeEdge('e2-1', 'n2', 'n1'),  // σ₂ → σ₁
		makeEdge('e1-3', 'n1', 'n3'),  // σ₁ → σ₃
		makeEdge('e2-3', 'n2', 'n3'),  // σ₂ → σ₃
		makeEdge('e3-4', 'n3', 'n4'),  // σ₃ → env_out
	],
	systemState: {
		name: '2N Generator',
		div: [],
		dsv: []
	}
};

// ─── Even Parity Checker ─────────────────────────────────────────────────────
// Accepts strings with an even number of 1s.
// Neuron σ₁ (Input): Spike stream.
// Neuron σ₂ (Parity): Forgetting rule a² → λ consumes pairs of spikes.
// Spiking rule a → a; 0 signals odd parity to output.
// ────────────────────────────────────────────────────────────────────────────────
const evenParityChecker: GallerySystem = {
	id: 'even-parity-checker',
	title: 'Even Parity Checker',
	description: 'String computation system that accepts bitstrings with even parity. Uses forgetting rules to consume pairs of spikes.',
	category: 'string-languages',
	nodes: [
		{
			id: 'n1',
			type: 'neuron',
			position: { x: 100, y: 200 },
			data: {
				id: 'in',
				neuronType: 'input',
				spikes: '11011',
				delay: 0,
				rules: []
			}
		},
		{
			id: 'n2',
			type: 'neuron',
			position: { x: 400, y: 200 },
			data: {
				id: '\\sigma_{parity}',
				neuronType: 'regular',
				spikes: 0,
				delay: 0,
				rules: ['a^2 \\to \\lambda', 'a \\to a; 0']
			}
		},
		{
			id: 'n3',
			type: 'neuron',
			position: { x: 700, y: 200 },
			data: {
				id: 'out',
				neuronType: 'output',
				spikes: '',
				delay: 0,
				rules: []
			}
		}
	],
	edges: [
		makeEdge('e1-2', 'n1', 'n2'),
		makeEdge('e2-3', 'n2', 'n3'),
	],
	systemState: {
		name: 'Even Parity Checker',
		div: [],
		dsv: []
	}
};

// ─── Multiples of 3 Generator ────────────────────────────────────────────────
// Generates spike trains representing multiples of 3.
// ────────────────────────────────────────────────────────────────────────────────
const multiplesOf3Generator: GallerySystem = {
	id: 'multiples-of-3',
	title: 'Multiples of 3 Generator',
	description: 'Generates a spike train for multiples of 3. Uses a complex interaction of delays and forgetting rules.',
	category: 'string-languages',
	nodes: [
		{
			id: 'n1',
			type: 'neuron',
			position: { x: 100, y: 150 },
			data: {
				id: '\\sigma_1',
				neuronType: 'regular',
				spikes: 3,
				delay: 0,
				rules: ['a^3/a \\to a; 2', 'a \\to \\lambda']
			}
		},
		{
			id: 'n2',
			type: 'neuron',
			position: { x: 400, y: 300 },
			data: {
				id: '\\sigma_2',
				neuronType: 'regular',
				spikes: 1,
				delay: 0,
				rules: ['a \\to a; 1', 'a \\to a; 3']
			}
		},
		{
			id: 'n3',
			type: 'neuron',
			position: { x: 600, y: 100 },
			data: {
				id: '\\sigma_3',
				neuronType: 'regular',
				spikes: 4,
				delay: 0,
				rules: ['a^4 \\to a; 0', 'a \\to a; 3', 'a^3 \\to \\lambda']
			}
		},
		{
			id: 'n4',
			type: 'neuron',
			position: { x: 900, y: 200 },
			data: {
				id: 'env_{out}',
				neuronType: 'output',
				spikes: '',
				delay: 0,
				rules: []
			}
		}
	],
	edges: [
		makeEdge('e1-2', 'n1', 'n2'),
		makeEdge('e2-1', 'n2', 'n1'),
		makeEdge('e1-3', 'n1', 'n3'),
		makeEdge('e2-3', 'n2', 'n3'),
		makeEdge('e3-4', 'n3', 'n4'),
	],
	systemState: {
		name: 'Multiples of 3 Generator',
		div: [],
		dsv: []
	}
};

// ─── System Pi_1 (Research Paper) ───────────────────────────────────────────
// The system described in Fig. 1 of "On String Languages Generated by Spiking 
// Neural P Systems". Demonstrates complex non-deterministic branching.
// ────────────────────────────────────────────────────────────────────────────────
const pi1System: GallerySystem = {
	id: 'pi1-system',
	title: 'System Pi_1',
	description: 'A finite SN P system from the research literature (Fig. 1). Demonstrates non-deterministic rule selection and complex configuration graphs.',
	category: 'string-languages',
	nodes: [
		{
			id: 'n1',
			type: 'neuron',
			position: { x: 150, y: 150 },
			data: {
				id: '1',
				neuronType: 'regular',
				spikes: 1,
				delay: 0,
				rules: ['a \\to a; 0', 'a \\to a; 1']
			}
		},
		{
			id: 'n2',
			type: 'neuron',
			position: { x: 550, y: 150 },
			data: {
				id: '2',
				neuronType: 'regular',
				spikes: 1,
				delay: 0,
				rules: ['a \\to a; 0', 'a \\to a; 1']
			}
		},
		{
			id: 'n3',
			type: 'neuron',
			position: { x: 350, y: 350 },
			data: {
				id: '3',
				neuronType: 'regular',
				spikes: 2,
				delay: 0,
				rules: ['a \\to a; 0', 'a^2 \\to \\lambda']
			}
		}
	],
	edges: [
		makeEdge('e1-2', 'n1', 'n2'),
		makeEdge('e1-3', 'n1', 'n3'),
		makeEdge('e2-1', 'n2', 'n1'),
		makeEdge('e2-3', 'n2', 'n3'),
		makeEdge('e3-1', 'n3', 'n1'),
	],
	systemState: {
		name: 'System Pi_1',
		div: [],
		dsv: []
	}
};

// ─── One Spike Chain (Πosc) ──────────────────────────────────────────────────
// Stress testing benchmark from WebSnapse Reloaded.
// Linear chain where only the first node has a spike.
// ────────────────────────────────────────────────────────────────────────────────
const oneSpikeChain: GallerySystem = {
	id: 'one-spike-chain',
	title: 'One Spike Chain (Stress Test)',
	description: 'Performance benchmark system (Πosc). A linear chain of 10 neurons where a single spike is passed sequentially.',
	category: 'stress-tests',
	nodes: Array.from({ length: 10 }).map((_, i) => ({
		id: `osc${i}`,
		type: 'neuron',
		position: { x: 100 + i * 150, y: 250 },
		data: {
			id: `\\sigma_{${i + 1}}`,
			neuronType: i === 9 ? 'output' : 'regular',
			spikes: i === 0 ? 1 : 0,
			delay: 0,
			rules: i === 9 ? [] : ['a/a \\to a; 0']
		}
	})),
	edges: Array.from({ length: 9 }).map((_, i) => makeEdge(`e${i}-${i + 1}`, `osc${i}`, `osc${i + 1}`)),
	systemState: {
		name: 'One Spike Chain',
		div: [],
		dsv: []
	}
};

// ─── All Spike Chain (Πasc) ──────────────────────────────────────────────────
// Stress testing benchmark from WebSnapse Reloaded.
// Linear chain where every node starts with a spike.
// ────────────────────────────────────────────────────────────────────────────────
const allSpikeChain: GallerySystem = {
	id: 'all-spike-chain',
	title: 'All Spike Chain (Stress Test)',
	description: 'Performance benchmark system (Πasc). Every neuron in the 10-node chain fires simultaneously at each step.',
	category: 'stress-tests',
	nodes: Array.from({ length: 10 }).map((_, i) => ({
		id: `asc${i}`,
		type: 'neuron',
		position: { x: 100 + i * 150, y: 250 },
		data: {
			id: `\\sigma_{${i + 1}}`,
			neuronType: i === 9 ? 'output' : 'regular',
			spikes: 1,
			delay: 0,
			rules: i === 9 ? [] : ['a^+/a \\to a; 0']
		}
	})),
	edges: Array.from({ length: 9 }).map((_, i) => makeEdge(`e${i}-${i + 1}`, `asc${i}`, `asc${i + 1}`)),
	systemState: {
		name: 'All Spike Chain',
		div: [],
		dsv: []
	}
};

// ─── Simple Complete (Πsc) ───────────────────────────────────────────────────
// Stress testing benchmark with a fully connected graph.
// ────────────────────────────────────────────────────────────────────────────────
const simpleComplete: GallerySystem = {
	id: 'simple-complete',
	title: 'Simple Complete (Stress Test)',
	description: 'Performance benchmark (Πsc) using a fully connected 8-node system without non-determinism.',
	category: 'stress-tests',
	nodes: Array.from({ length: 8 }).map((_, i) => ({
		id: `sc${i}`,
		type: 'neuron',
		position: { x: 400 + 250 * Math.cos((i * 2 * Math.PI) / 8), y: 300 + 250 * Math.sin((i * 2 * Math.PI) / 8) },
		data: {
			id: `\\sigma_{${i + 1}}`,
			neuronType: 'regular',
			spikes: 2,
			delay: 0,
			rules: ['a^2/a \\to a; 0']
		}
	})),
	edges: Array.from({ length: 8 }).flatMap((_, i) => 
		Array.from({ length: 8 }).filter((_, j) => i !== j).map((_, j) => makeEdge(`e${i}-${j}`, `sc${i}`, `sc${j}`))
	),
	systemState: {
		name: 'Simple Complete',
		div: [],
		dsv: []
	}
};

// ─── Benchmark Complete (Πbc) ────────────────────────────────────────────────
// Stress testing benchmark with a fully connected graph and non-determinism.
// ────────────────────────────────────────────────────────────────────────────────
const benchmarkComplete: GallerySystem = {
	id: 'benchmark-complete',
	title: 'Benchmark Complete (Stress Test)',
	description: 'Performance benchmark (Πbc) using a fully connected 8-node system with non-deterministic spiking rules.',
	category: 'stress-tests',
	nodes: Array.from({ length: 8 }).map((_, i) => ({
		id: `bc${i}`,
		type: 'neuron',
		position: { x: 400 + 250 * Math.cos((i * 2 * Math.PI) / 8), y: 300 + 250 * Math.sin((i * 2 * Math.PI) / 8) },
		data: {
			id: `\\sigma_{${i + 1}}`,
			neuronType: 'regular',
			spikes: 2,
			delay: 0,
			rules: ['(a^2)^*/a \\to a', '(a^2)^*/a^2 \\to a^2']
		}
	})),
	edges: Array.from({ length: 8 }).flatMap((_, i) => 
		Array.from({ length: 8 }).filter((_, j) => i !== j).map((_, j) => makeEdge(`e${i}-${j}`, `bc${i}`, `bc${j}`))
	),
	systemState: {
		name: 'Benchmark Complete',
		div: [],
		dsv: []
	}
};

// ─── Bit Adder (Serial) ────────────────────────────────────────────────────────
// Bitwise serial binary adder.
// Two input neurons feed bitstrings into a single adder neuron (add_{0,1}).
// Adder rules:  a → a; 0,   a²/a → λ,   a³/a² → a; 0
// Output neuron collects the addition result.
// ────────────────────────────────────────────────────────────────────────────────
const bitAdderSerial: GallerySystem = {
	id: 'bit-adder-serial',
	title: 'Bit Adder (Serial)',
	description: 'Bitwise serial binary adder using neuron add_{0,1} with spiking/forgetting rules for carry propagation.',
	category: 'arithmetic',
	nodes: [
		{
			id: 'n1',
			type: 'neuron',
			position: { x: 150, y: 100 },
			data: {
				id: 'in_0',
				neuronType: 'input',
				spikes: '111',
				delay: 0,
				rules: []
			}
		},
		{
			id: 'n2',
			type: 'neuron',
			position: { x: 150, y: 350 },
			data: {
				id: 'in_1',
				neuronType: 'input',
				spikes: '1101',
				delay: 0,
				rules: []
			}
		},
		{
			id: 'n3',
			type: 'neuron',
			position: { x: 450, y: 225 },
			data: {
				id: 'add_{0,1}',
				neuronType: 'regular',
				spikes: 0,
				delay: 0,
				rules: ['a \\to a; 0', 'a^2/a \\to \\lambda', 'a^3/a^2 \\to a; 0']
			}
		},
		{
			id: 'n4',
			type: 'neuron',
			position: { x: 750, y: 225 },
			data: {
				id: 'out',
				neuronType: 'output',
				spikes: '',
				delay: 0,
				rules: []
			}
		}
	],
	edges: [
		makeEdge('e1-3', 'n1', 'n3'),  // in_0 → add
		makeEdge('e2-3', 'n2', 'n3'),  // in_1 → add
		makeEdge('e3-4', 'n3', 'n4'),  // add  → out
	],
	systemState: {
		name: 'Bit Adder (Serial)',
		div: [],
		dsv: []
	}
};

// ─── Comparator ────────────────────────────────────────────────────────────────
// Compares two binary inputs and outputs which is larger or if they are equal.
// Two input neurons (a, b) feed into:
//   - "one" neuron: forgetting-based detection, rules: a² → λ, a → a; 0
//   - "both" neuron: joint-signal detection, rules: a² → a; 0, a → λ
// Two output neurons: "max" and "min".
// ────────────────────────────────────────────────────────────────────────────────
const comparator: GallerySystem = {
	id: 'comparator',
	title: 'Comparator',
	description: 'Compares two binary inputs and determines which is larger, or if they are equal, using "one" and "both" detector neurons.',
	category: 'comparators',
	nodes: [
		{
			id: 'n1',
			type: 'neuron',
			position: { x: 150, y: 80 },
			data: {
				id: 'a',
				neuronType: 'input',
				spikes: '1111',
				delay: 0,
				rules: []
			}
		},
		{
			id: 'n2',
			type: 'neuron',
			position: { x: 150, y: 380 },
			data: {
				id: 'b',
				neuronType: 'input',
				spikes: '11',
				delay: 0,
				rules: []
			}
		},
		{
			id: 'n3',
			type: 'neuron',
			position: { x: 450, y: 100 },
			data: {
				id: 'one',
				neuronType: 'regular',
				spikes: 0,
				delay: 0,
				rules: ['a^2 \\to \\lambda', 'a \\to a; 0']
			}
		},
		{
			id: 'n4',
			type: 'neuron',
			position: { x: 450, y: 360 },
			data: {
				id: 'both',
				neuronType: 'regular',
				spikes: 0,
				delay: 0,
				rules: ['a^2 \\to a; 0', 'a \\to \\lambda']
			}
		},
		{
			id: 'n5',
			type: 'neuron',
			position: { x: 750, y: 100 },
			data: {
				id: 'max',
				neuronType: 'output',
				spikes: '',
				delay: 0,
				rules: []
			}
		},
		{
			id: 'n6',
			type: 'neuron',
			position: { x: 750, y: 360 },
			data: {
				id: 'min',
				neuronType: 'output',
				spikes: '',
				delay: 0,
				rules: []
			}
		}
	],
	edges: [
		makeEdge('e1-3', 'n1', 'n3'),  // a → one
		makeEdge('e1-4', 'n1', 'n4'),  // a → both
		makeEdge('e2-3', 'n2', 'n3'),  // b → one
		makeEdge('e2-4', 'n2', 'n4'),  // b → both
		makeEdge('e3-5', 'n3', 'n5'),  // one  → max
		makeEdge('e4-5', 'n4', 'n5'),  // both → max
		makeEdge('e4-6', 'n4', 'n6'),  // both → min
	],
	systemState: {
		name: 'Comparator',
		div: [],
		dsv: []
	}
};

// ─── Export Gallery ─────────────────────────────────────────────────────────────
export const GALLERY_SYSTEMS: GallerySystem[] = [
	pi1System,
	twoNGenerator,
	evenParityChecker,
	multiplesOf3Generator,
	oneSpikeChain,
	allSpikeChain,
	simpleComplete,
	benchmarkComplete,
	bitAdderSerial,
	comparator
];

export const GALLERY_CATEGORIES = [
	{ id: 'all', label: 'All Systems' },
	{ id: 'generators', label: 'Generators' },
	{ id: 'string-languages', label: 'String Languages' },
	{ id: 'stress-tests', label: 'Stress Tests' },
	{ id: 'arithmetic', label: 'Arithmetic' },
	{ id: 'comparators', label: 'Comparators' },
] as const;
