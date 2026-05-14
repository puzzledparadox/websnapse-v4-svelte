<!--
	@component
	BranchModal.svelte
	
	Renders an overlay modal when the engine encounters a non-deterministic
	branching point (multiple valid rules can fire, leading to different states).
	Allows the user to manually select which execution path to follow for the
	next simulation tick.
-->
<script lang="ts">
	import Katex from 'svelte-katex';
	import { GitBranch } from 'lucide-svelte';
	import 'katex/dist/katex.min.css';

	let {
		possibilities = [],
		nodes = [],
		tick = 0,
		onSelect = (_pos: any) => {}
	}: {
		possibilities: any[];
		nodes: any[];
		tick: number;
		onSelect: (pos: any) => void;
	} = $props();

	/**
	 * Builds a flattened, ordered list of all rules across all regular neurons.
	 * This order strictly mirrors the array structure used by the matrix engine.
	 * 
	 * @returns Array of objects containing the owning neuron's ID and the rule string.
	 */
	function getOrderedRules(): { neuronId: string; rule: string }[] {
		const out: { neuronId: string; rule: string }[] = [];
		nodes.forEach((n) => {
			const t = n.data?.neuronType;
			if (t === 'input' || t === 'Input' || t === 'output' || t === 'Output') return;
			(n.data?.rules || []).forEach((r: string) => out.push({ neuronId: n.id, rule: r }));
		});
		return out;
	}

	/**
	 * Identifies which specific rules were selected in a given non-deterministic branch.
	 * Filters out rules that are selected across ALL branches to highlight only the conflicts.
	 * 
	 * @param pos - A single possibility state object from the engine.
	 * @returns Array of the conflicting rules that are active in this specific branch.
	 */
	function getSelectedRules(pos: any): { neuronId: string; rule: string }[] {
		const ordered = getOrderedRules();
		const selected: { neuronId: string; rule: string }[] = [];

		// Find indices where selection differs across possibilities (the branch points)
		const conflictIndices = new Set<number>();
		if (possibilities.length > 1) {
			for (let i = 0; i < ordered.length; i++) {
				const first = possibilities[0].dv?.[i];
				if (possibilities.some((p) => p.dv?.[i] !== first)) {
					conflictIndices.add(i);
				}
			}
		}

		(pos.dv || []).forEach((v: number, i: number) => {
			if (v === 1 && conflictIndices.has(i) && ordered[i]) {
				selected.push(ordered[i]);
			}
		});
		return selected;
	}

	/**
	 * Reactively computes the list of neuron IDs that are currently experiencing
	 * a non-deterministic conflict (where different rules are chosen across branches).
	 */
	let conflictingNeurons = $derived.by(() => {
		const ordered = getOrderedRules();
		const neurons = new Set<string>();
		if (possibilities.length > 1) {
			for (let i = 0; i < ordered.length; i++) {
				const first = possibilities[0].dv?.[i];
				if (possibilities.some((p) => p.dv?.[i] !== first)) {
					neurons.add(ordered[i].neuronId);
				}
			}
		}
		return Array.from(neurons);
	});
</script>

{#if possibilities.length > 1}
	<!-- Full-canvas overlay -->
	<div class="branch-overlay">
		<div class="branch-modal">
			<!-- Header -->
			<div class="branch-header">
				<div class="branch-header-icon">
					<GitBranch size={20} />
				</div>
				<div>
					<h2 class="branch-title">
						Conflict in {conflictingNeurons.length === 1 ? 'Neuron' : 'Neurons'}
						<span class="conflicting-ids">
							{conflictingNeurons.join(', ')}
						</span>
					</h2>
					<p class="branch-subtitle">
						Tick {tick} &rarr; Resolve non-determinism to continue
					</p>
				</div>
				<span class="branch-count-badge">{possibilities.length} options</span>
			</div>

			<!-- Branch cards -->
			<div class="branch-cards">
				{#each possibilities as pos, i}
					{@const decisionRules = getSelectedRules(pos)}
					<button class="branch-card" onclick={() => onSelect(pos)}>
						<!-- Card header -->
						<div class="branch-card-header">
							<span class="branch-num">Option {i + 1}</span>
							{#if pos.is_halted}
								<span class="badge-halt">Halts</span>
							{/if}
						</div>

						<!-- Decision rules section -->
						<div class="branch-section">
							<div class="branch-section-label">Selected Rule(s)</div>
							{#if decisionRules.length === 0}
								<span class="no-rules">no rule fires</span>
							{:else}
								{#each decisionRules as { neuronId, rule }}
									<div class="rule-row">
										<span class="rule-neuron"><Katex>{neuronId}</Katex></span>
										<span class="rule-colon">:</span>
										<span class="rule-expr"><Katex>{rule}</Katex></span>
									</div>
								{/each}
							{/if}
						</div>

						<div class="branch-cta">Select Option &rarr;</div>
					</button>
				{/each}
			</div>

			<p class="branch-hint">Resolution will update system state for tick {tick + 1}</p>
		</div>
	</div>
{/if}

<style>
	/* ─── Overlay backdrop ─── */
	.branch-overlay {
		position: absolute;
		inset: 0;
		z-index: 60;
		display: flex;
		align-items: center;
		justify-content: center;
		padding: 24px;
		background: rgba(8, 5, 20, 0.7);
		backdrop-filter: blur(6px);
		-webkit-backdrop-filter: blur(6px);
	}

	/* ─── Modal card ─── */
	.branch-modal {
		background: rgba(16, 12, 32, 0.97);
		border: 1px solid rgba(168, 85, 247, 0.3);
		border-radius: 20px;
		box-shadow:
			0 0 0 1px rgba(168, 85, 247, 0.1),
			0 24px 64px rgba(0, 0, 0, 0.55),
			0 0 80px rgba(124, 58, 237, 0.1);
		max-width: min(92vw, 900px);
		width: max-content;
		overflow: hidden;
	}

	/* ─── Header ─── */
	.branch-header {
		display: flex;
		align-items: center;
		gap: 14px;
		padding: 18px 24px 16px;
		border-bottom: 1px solid rgba(168, 85, 247, 0.18);
		background: linear-gradient(135deg, rgba(124, 58, 237, 0.14) 0%, rgba(168, 85, 247, 0.06) 100%);
	}

	.branch-header-icon {
		flex-shrink: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 40px;
		height: 40px;
		border-radius: 10px;
		background: linear-gradient(135deg, #7c3aed, #a855f7);
		color: white;
		box-shadow: 0 4px 14px rgba(124, 58, 237, 0.45);
	}

	.branch-title {
		font-size: 15px;
		font-weight: 700;
		color: #f0e8ff;
		margin: 0;
		line-height: 1.2;
	}

	.branch-subtitle {
		font-size: 12px;
		color: rgba(192, 168, 240, 0.65);
		margin: 3px 0 0;
	}

	.conflicting-ids {
		color: #a78bfa;
		background: rgba(167, 139, 250, 0.1);
		padding: 1px 6px;
		border-radius: 4px;
		margin-left: 4px;
		font-family: monospace;
	}

	.branch-count-badge {
		margin-left: auto;
		flex-shrink: 0;
		background: rgba(168, 85, 247, 0.18);
		border: 1px solid rgba(168, 85, 247, 0.3);
		color: #c4b5fd;
		font-size: 11px;
		font-weight: 600;
		padding: 3px 11px;
		border-radius: 20px;
	}

	/* ─── Cards row ─── */
	.branch-cards {
		display: flex;
		flex-wrap: wrap;
		gap: 14px;
		padding: 20px 24px;
		max-height: 58vh;
		overflow-y: auto;
		justify-content: center;
	}

	/* ─── Single branch card ─── */
	.branch-card {
		display: flex;
		flex-direction: column;
		gap: 10px;
		background: rgba(255, 255, 255, 0.035);
		border: 1px solid rgba(168, 85, 247, 0.18);
		border-radius: 14px;
		padding: 15px;
		min-width: 190px;
		max-width: 250px;
		cursor: pointer;
		text-align: left;
		transition:
			background 0.18s ease,
			border-color 0.18s ease,
			box-shadow 0.18s ease,
			transform 0.18s ease;
		color: inherit;
		font: inherit;
	}

	.branch-card:hover {
		background: rgba(168, 85, 247, 0.1);
		border-color: rgba(168, 85, 247, 0.55);
		box-shadow:
			0 0 0 2px rgba(168, 85, 247, 0.28),
			0 8px 28px rgba(124, 58, 237, 0.22);
		transform: translateY(-3px);
	}

	.branch-card:active {
		transform: translateY(0);
	}

	.branch-card-header {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 8px;
	}

	.branch-num {
		font-size: 13px;
		font-weight: 700;
		color: #c4b5fd;
		letter-spacing: 0.02em;
	}

	.badge-halt {
		font-size: 10px;
		font-weight: 600;
		background: rgba(239, 68, 68, 0.18);
		border: 1px solid rgba(239, 68, 68, 0.38);
		color: #fca5a5;
		padding: 2px 7px;
		border-radius: 10px;
	}

	/* ─── Section ─── */
	.branch-section {
		border-top: 1px solid rgba(168, 85, 247, 0.1);
		padding-top: 9px;
	}

	.branch-section-label {
		font-size: 10px;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: rgba(196, 181, 253, 0.45);
		margin-bottom: 6px;
	}

	/* ─── Rules ─── */
	.no-rules {
		font-size: 11px;
		color: rgba(196, 181, 253, 0.35);
		font-style: italic;
	}

	.rule-row {
		display: flex;
		align-items: baseline;
		gap: 4px;
		flex-wrap: wrap;
		margin-bottom: 3px;
	}

	.rule-neuron {
		font-size: 12px;
		color: #a78bfa;
		font-weight: 600;
	}

	.rule-colon {
		font-size: 12px;
		color: rgba(196, 181, 253, 0.35);
	}

	.rule-expr {
		font-size: 12px;
		color: #e2d9f3;
	}


	/* ─── CTA hint ─── */
	.branch-cta {
		font-size: 11px;
		color: rgba(196, 181, 253, 0.35);
		text-align: center;
		margin-top: auto;
		opacity: 0;
		transition: opacity 0.15s ease;
	}

	.branch-card:hover .branch-cta {
		opacity: 1;
		color: #c4b5fd;
	}

	/* ─── Bottom hint ─── */
	.branch-hint {
		text-align: center;
		font-size: 11px;
		color: rgba(196, 181, 253, 0.3);
		padding: 0 24px 16px;
		margin: 0;
	}
</style>
