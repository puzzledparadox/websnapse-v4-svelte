import { showToast } from '../components/Toast.svelte';

/**
 * BenchmarkService
 * 
 * Formal performance tracking for WebSnapse v4.
 * Measures Load Time, Next-Config Compute Time, and DOM Re-render Time.
 */
export class BenchmarkService {
	metrics = $state({
		loadTimes: [] as number[],
		computeTimes: [] as number[],
		renderTimes: [] as number[]
	});

	private startTime: number = 0;
	private computeStartTime: number = 0;
	private renderStartTime: number = 0;

	// Load Time Tracking
	startLoad() {
		this.startTime = performance.now();
		console.log('[Benchmark] Loading system...');
	}

	endLoad() {
		const duration = performance.now() - this.startTime;
		this.metrics.loadTimes.push(duration);
		console.log(`[Benchmark] System Loaded in ${duration.toFixed(2)}ms`);
		showToast(`Load Time: ${duration.toFixed(2)}ms`, 'info');
	}

	// Compute Time Tracking
	startCompute() {
		this.computeStartTime = performance.now();
	}

	endCompute() {
		const duration = performance.now() - this.computeStartTime;
		this.metrics.computeTimes.push(duration);
		console.log(`[Benchmark] Compute Time: ${duration.toFixed(2)}ms`);
	}

	// Render Time Tracking
	startRender() {
		this.renderStartTime = performance.now();
	}

	endRender() {
		const duration = performance.now() - this.renderStartTime;
		this.metrics.renderTimes.push(duration);
		console.log(`[Benchmark] Render Time: ${duration.toFixed(2)}ms`);
	}

	/**
	 * Calculates and prints a full benchmarking report to the console.
	 */
	printReport() {
		const avg = (arr: number[]) => arr.length > 0 ? (arr.reduce((a, b) => a + b, 0) / arr.length).toFixed(2) : 'N/A';
		
		const report = `
╔══════════════════════════════════════════════════════════════╗
║                WEBSNAPSE v4 BENCHMARK REPORT                 ║
╠══════════════════════════════════════════════════════════════╣
  Initial Load Time (Avg):    ${avg(this.metrics.loadTimes)} ms
  Next-Config Compute (Avg):   ${avg(this.metrics.computeTimes)} ms
  Average Re-render Time:     ${avg(this.metrics.renderTimes)} ms
╠══════════════════════════════════════════════════════════════╣
  Samples Collected:
  - Loads: ${this.metrics.loadTimes.length}
  - Ticks: ${this.metrics.computeTimes.length}
╚══════════════════════════════════════════════════════════════╝
		`;
		console.log(report);
		showToast(`Benchmark: ${avg(this.metrics.renderTimes)}ms avg render`, 'info');
	}

	clear() {
		this.metrics.loadTimes = [];
		this.metrics.computeTimes = [];
		this.metrics.renderTimes = [];
		console.log('[Benchmark] Metrics cleared.');
	}
}

export const benchmark = new BenchmarkService();

// Expose globally for easy console access
if (typeof window !== 'undefined') {
	(window as any).benchmark = benchmark;
}
