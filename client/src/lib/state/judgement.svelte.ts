import { simulation } from '$lib/services/simulation.svelte';

export class JudgementState {
	testStrings = $state([
		{ value: '11', status: 'idle' },
		{ value: '101', status: 'idle' },
		{ value: '1', status: 'idle' }
	]);
	timeLimit = $state(100);

	addString() {
		this.testStrings.push({ value: '', status: 'idle' });
	}

	removeString(index: number) {
		this.testStrings.splice(index, 1);
	}

	async handleJudge() {
		simulation.judgeResults = {};

		for (let str of this.testStrings) {
			str.status = 'judging';
			simulation.sendState({
				type: 'judge',
				string: str.value,
				timeLimit: this.timeLimit,
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

	// This should be called in an $effect block in a component
	syncResults() {
		for (let str of this.testStrings) {
			if (simulation.judgeResults[str.value]) {
				str.status = simulation.judgeResults[str.value];
			}
		}
	}
}

export const judgementState = new JudgementState();
