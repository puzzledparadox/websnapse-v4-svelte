<script lang="ts">
	import { 
		MousePointer2, 
		PlusCircle, 
		ArrowRight, 
		Trash2, 
		Hand, 
		ShieldAlert,
		History 
	} from 'lucide-svelte';

	let { activeTool = $bindable('select'), showHistory = $bindable(false), onClear } = $props();

	const tools = [
		{ id: 'select', icon: MousePointer2, label: 'Select (V)' },
		{ id: 'node', icon: PlusCircle, label: 'Neuron (N)' },
		{ id: 'edge', icon: ArrowRight, label: 'Synapse (E)' },
		{ id: 'delete', icon: Trash2, label: 'Delete (Del)' },
		{ id: 'hand', icon: Hand, label: 'Pan (H)' }
	];

	function handleKeydown(e: KeyboardEvent) {
		// Keyboard shortcuts (optional but nice for engineering tools)
		if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
		
		switch(e.key.toLowerCase()) {
			case 'v': activeTool = 'select'; break;
			case 'n': activeTool = 'node'; break;
			case 'e': activeTool = 'edge'; break;
			case 'h': activeTool = 'hand'; break;
			case 'delete':
			case 'backspace':
				activeTool = 'delete'; break;
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

<!-- Horizontal toolbar docked at top center of the canvas area -->
<div class="absolute left-1/2 top-4 z-50 flex -translate-x-1/2 items-center gap-2 rounded-lg border border-gray-300 bg-gray-50 px-3 py-2 shadow-md">
	<div class="mr-1 border-r border-gray-300 pr-2 text-xs font-bold text-gray-500">
		TOOLS
	</div>

	{#each tools as tool}
		<button
			class="group relative flex h-10 w-10 items-center justify-center rounded-md border transition-colors
				{activeTool === tool.id 
					? 'bg-purple-100 border-purple-500 text-purple-700 shadow-sm' 
					: 'border-transparent bg-transparent text-gray-600 hover:bg-gray-200 hover:text-gray-900'}"
			onclick={() => activeTool = tool.id}
			title={tool.label}
		>
			<tool.icon size={20} />
			
			<!-- Tooltip (below) -->
			<div class="pointer-events-none absolute top-full mt-2 whitespace-nowrap rounded bg-gray-800 px-2 py-1 text-xs font-medium text-white opacity-0 transition-opacity group-hover:opacity-100">
				{tool.label}
			</div>
		</button>
	{/each}

	<div class="mx-1 h-6 border-l border-gray-300"></div>

	<button
		class="group relative flex h-10 w-10 items-center justify-center rounded-md border transition-colors
			{showHistory 
				? 'bg-blue-100 border-blue-500 text-blue-700 shadow-sm' 
				: 'border-transparent bg-transparent text-gray-600 hover:bg-gray-200 hover:text-gray-900'}"
		onclick={() => showHistory = !showHistory}
		title="Toggle History"
	>
		<History size={20} />
		
		<div class="pointer-events-none absolute top-full mt-2 whitespace-nowrap rounded bg-gray-800 px-2 py-1 text-xs font-medium text-white opacity-0 transition-opacity group-hover:opacity-100">
			Toggle History
		</div>
	</button>

	<div class="mx-1 h-6 border-l border-gray-300"></div>

	<button
		class="group relative flex h-10 w-10 items-center justify-center rounded-md border border-transparent bg-transparent text-red-600 transition-colors hover:bg-red-100 hover:border-red-300"
		onclick={() => onClear()}
		title="Clear Canvas"
	>
		<ShieldAlert size={20} />
		
		<div class="pointer-events-none absolute top-full mt-2 whitespace-nowrap rounded bg-red-800 px-2 py-1 text-xs font-medium text-white opacity-0 transition-opacity group-hover:opacity-100">
			Clear Canvas
		</div>
	</button>
</div>


