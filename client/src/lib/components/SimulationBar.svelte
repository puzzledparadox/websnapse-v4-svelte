<script lang="ts">
	import {
		Play,
		Pause,
		SkipBack,
		SkipForward,
		Shuffle,
		RotateCcw,
		Compass
	} from 'lucide-svelte';

	let {
		isConnected = false,
		isPlaying = $bindable(false),
		onStep = () => {},
		onStepBack = () => {},
		onPlayPause = () => {},
		onRestart = () => {},
		onModeChange = (mode: 'pseudorandom' | 'guided') => {},
		onSpeedChange = (speed: number) => {}
	} = $props();
	let mode = $state<'pseudorandom' | 'guided'>('pseudorandom');
	let speed = $state(1.5);

	const speedMin = 0.25;
	const speedMax = 5;
	const speedStep = 0.25;

	// Computed: slider fill percentage
	let fillPercent = $derived(((speed - speedMin) / (speedMax - speedMin)) * 100);

	function togglePlay() {
		isPlaying = !isPlaying;
		onPlayPause();
	}

	function toggleMode() {
		mode = mode === 'pseudorandom' ? 'guided' : 'pseudorandom';
		onModeChange(mode);
	}

	function handleSpeedInput(e: Event) {
		speed = parseFloat((e.target as HTMLInputElement).value);
		onSpeedChange(speed);
	}

	function handleRestart() {
		isPlaying = false;
		onRestart();
	}

	function handleStepForward() {
		onStep();
	}

	function handleStepBack() {
		onStepBack();
	}
</script>

<!-- Simulation Options Bar — bottom center of canvas -->
<div class="sim-bar">
	<div class="sim-bar-inner">
		<!-- Top Row: Transport Controls -->
		<div class="transport-row">
			<!-- Mode Toggle (Pseudorandom / Guided) -->
			<button
				class="transport-btn mode-btn"
				class:active={mode === 'guided'}
				onclick={toggleMode}
				title={mode === 'pseudorandom' ? 'Pseudorandom Mode (click to switch to Guided)' : 'Guided Mode (click to switch to Pseudorandom)'}
			>
				{#if mode === 'pseudorandom'}
					<Shuffle size={18} />
				{:else}
					<Compass size={18} />
				{/if}

				<!-- Mode tooltip -->
				<div class="transport-tooltip">
					{mode === 'pseudorandom' ? 'Pseudorandom' : 'Guided'}
				</div>
			</button>

			<!-- Step Back -->
			<button
				class="transport-btn"
				onclick={handleStepBack}
				title="Step Back"
			>
				<SkipBack size={18} />
				<div class="transport-tooltip">Step Back</div>
			</button>

			<!-- Play / Pause -->
			<button
				class="play-btn"
				class:playing={isPlaying}
				onclick={togglePlay}
				title={isPlaying ? 'Pause Simulation' : 'Play Simulation'}
			>
				{#if isPlaying}
					<Pause size={24} />
				{:else}
					<Play size={24} class="play-icon-offset" />
				{/if}
			</button>

			<!-- Step Forward -->
			<button
				class="transport-btn"
				onclick={handleStepForward}
				title="Step Forward"
			>
				<SkipForward size={18} />
				<div class="transport-tooltip">Step Forward</div>
			</button>

			<!-- Restart -->
			<button
				class="transport-btn restart-btn"
				onclick={handleRestart}
				title="Restart Simulation"
			>
				<RotateCcw size={18} />
				<div class="transport-tooltip">Restart</div>
			</button>
		</div>

		<!-- Bottom Row: Speed Slider -->
		<div class="speed-row">
			<div class="speed-slider-wrap">
				<input
					type="range"
					min={speedMin}
					max={speedMax}
					step={speedStep}
					value={speed}
					oninput={handleSpeedInput}
					class="speed-slider"
					style="--fill: {fillPercent}%"
				/>
			</div>
			<span class="speed-label">{speed}x</span>
		</div>
	</div>
</div>

<style>
	/* ─── Container ─── */
	.sim-bar {
		position: absolute;
		bottom: 24px;
		left: 50%;
		transform: translateX(-50%);
		z-index: 50;
		pointer-events: auto;
	}

	.sim-bar-inner {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 8px;
		padding: 14px 22px 12px;
		background: rgba(255, 255, 255, 0.92);
		backdrop-filter: blur(14px);
		-webkit-backdrop-filter: blur(14px);
		border: 1px solid rgba(200, 200, 210, 0.45);
		border-radius: 16px;
		box-shadow:
			0 4px 24px rgba(0, 0, 0, 0.08),
			0 1px 4px rgba(0, 0, 0, 0.04);
	}

	/* ─── Transport Row ─── */
	.transport-row {
		display: flex;
		align-items: center;
		gap: 6px;
	}

	/* ─── Transport Buttons ─── */
	.transport-btn {
		position: relative;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 36px;
		height: 36px;
		border: none;
		background: transparent;
		color: #6b6b7b;
		border-radius: 10px;
		cursor: pointer;
		transition: all 0.2s ease;
	}

	.transport-btn:hover {
		background: rgba(168, 85, 247, 0.08);
		color: #7c3aed;
	}

	.transport-btn:active {
		transform: scale(0.92);
	}

	.transport-btn.active {
		color: #7c3aed;
		background: rgba(168, 85, 247, 0.12);
	}

	/* Mode-specific styling */
	.mode-btn.active {
		color: #7c3aed;
	}

	/* ─── Play Button ─── */
	.play-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 48px;
		height: 48px;
		margin: 0 4px;
		border: none;
		border-radius: 50%;
		background: linear-gradient(135deg, #a855f7 0%, #7c3aed 100%);
		color: white;
		cursor: pointer;
		box-shadow:
			0 2px 12px rgba(168, 85, 247, 0.35),
			0 1px 3px rgba(0, 0, 0, 0.1);
		transition: all 0.2s ease;
	}

	.play-btn:hover {
		background: linear-gradient(135deg, #9333ea 0%, #6d28d9 100%);
		box-shadow:
			0 4px 20px rgba(168, 85, 247, 0.45),
			0 2px 6px rgba(0, 0, 0, 0.12);
		transform: scale(1.06);
	}

	.play-btn:active {
		transform: scale(0.96);
	}

	.play-btn.playing {
		background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%);
		animation: pulse-glow 2s ease-in-out infinite;
	}

	@keyframes pulse-glow {
		0%, 100% { box-shadow: 0 2px 12px rgba(168, 85, 247, 0.35); }
		50% { box-shadow: 0 2px 24px rgba(168, 85, 247, 0.6); }
	}

	/* Slight offset for play icon (triangle needs visual centering) */
	:global(.play-icon-offset) {
		margin-left: 2px;
	}

	/* ─── Speed Row ─── */
	.speed-row {
		display: flex;
		align-items: center;
		gap: 8px;
		width: 100%;
	}

	.speed-slider-wrap {
		flex: 1;
		display: flex;
		align-items: center;
	}

	.speed-slider {
		-webkit-appearance: none;
		appearance: none;
		width: 100%;
		height: 5px;
		border-radius: 3px;
		outline: none;
		cursor: pointer;
		background: linear-gradient(
			to right,
			#c4b5fd 0%,
			#a855f7 var(--fill),
			#e5e5ea var(--fill),
			#e5e5ea 100%
		);
		transition: background 0.1s;
	}

	.speed-slider::-webkit-slider-thumb {
		-webkit-appearance: none;
		appearance: none;
		width: 14px;
		height: 14px;
		border-radius: 50%;
		background: #a855f7;
		border: 2px solid white;
		box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
		cursor: pointer;
		transition: transform 0.15s ease;
	}

	.speed-slider::-webkit-slider-thumb:hover {
		transform: scale(1.2);
	}

	.speed-slider::-moz-range-thumb {
		width: 14px;
		height: 14px;
		border-radius: 50%;
		background: #a855f7;
		border: 2px solid white;
		box-shadow: 0 1px 4px rgba(0, 0, 0, 0.15);
		cursor: pointer;
	}

	.speed-label {
		font-size: 12px;
		font-weight: 600;
		color: #7c3aed;
		min-width: 36px;
		text-align: center;
		font-variant-numeric: tabular-nums;
		user-select: none;
	}

	/* ─── Tooltips ─── */
	.transport-tooltip {
		position: absolute;
		top: 100%;
		left: 50%;
		transform: translateX(-50%);
		margin-top: 6px;
		padding: 4px 8px;
		background: #1f1f2e;
		color: white;
		font-size: 11px;
		font-weight: 500;
		border-radius: 6px;
		white-space: nowrap;
		pointer-events: none;
		opacity: 0;
		transition: opacity 0.15s ease;
	}

	.transport-btn:hover .transport-tooltip {
		opacity: 1;
	}
</style>
