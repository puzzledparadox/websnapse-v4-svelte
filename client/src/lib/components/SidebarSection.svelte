<!--
	@component
	SidebarSection.svelte
	
	A collapsible container for sidebar tools and panels.
	Provides a consistent header with a toggle icon and a content area.
-->
<script lang="ts">
	import { ChevronDown, ChevronRight, type Icon as LucideIcon } from 'lucide-svelte';
	import { slide } from 'svelte/transition';

	interface Props {
		title: string;
		icon?: any;
		isOpen?: boolean;
		children?: import('svelte').Snippet;
		class?: string;
		fill?: boolean;
		height?: number;
		minHeight?: number;
	}

	let { 
		title, 
		icon: Icon, 
		isOpen = $bindable(true), 
		children,
		class: className = "",
		fill = false,
		height = $bindable(0),
		minHeight = 100
	} = $props<Props>();

	let isResizing = $state(false);
	let sectionElement = $state<HTMLElement | null>(null);

	function toggle() {
		isOpen = !isOpen;
	}

	function startResizing(e: MouseEvent) {
		if (!height || !isOpen) return;
		isResizing = true;
		document.body.style.cursor = 'row-resize';
		document.body.style.userSelect = 'none';
		window.addEventListener('mousemove', handleMouseMove);
		window.addEventListener('mouseup', stopResizing);
	}

	function handleMouseMove(e: MouseEvent) {
		if (!isResizing || !sectionElement) return;
		const rect = sectionElement.getBoundingClientRect();
		const newHeight = e.clientY - rect.top - 44; // 44 is header height approx
		height = Math.max(minHeight, newHeight);
	}

	function stopResizing() {
		isResizing = false;
		document.body.style.cursor = '';
		document.body.style.userSelect = 'auto';
		window.removeEventListener('mousemove', handleMouseMove);
		window.removeEventListener('mouseup', stopResizing);
	}
</script>

<div 
	bind:this={sectionElement}
	class="flex flex-col border-b border-gray-100 last:border-0 {fill ? 'flex-1 min-h-0' : ''} {className}"
>
	<!-- Header -->
	<button
		onclick={toggle}
		class="flex h-11 w-full flex-shrink-0 items-center justify-between px-4 text-left transition-colors hover:bg-gray-50/80 focus-visible:bg-purple-50 focus-visible:outline-none"
		aria-expanded={isOpen}
	>
		<div class="flex items-center gap-2.5">
			{#if Icon}
				<div class="flex h-5 w-5 items-center justify-center text-gray-400 group-hover:text-purple-500">
					<Icon size={16} />
				</div>
			{/if}
			<span class="text-xs font-bold uppercase tracking-wider text-gray-500">{title}</span>
		</div>
		<div class="text-gray-400">
			{#if isOpen}
				<ChevronDown size={14} />
			{:else}
				<ChevronRight size={14} />
			{/if}
		</div>
	</button>

	<!-- Content -->
	{#if isOpen}
		<div 
			transition:slide={{ duration: 200 }}
			class="relative flex flex-col overflow-hidden {fill ? 'flex-1' : ''}"
			style={height > 0 ? `height: ${height}px;` : ''}
		>
			<div class="flex-1 overflow-y-auto px-4 pb-4 custom-scrollbar">
				{@render children?.()}
			</div>

			{#if height > 0}
				<div 
					class="absolute bottom-0 left-0 h-1 w-full cursor-row-resize transition-colors hover:bg-purple-400/30"
					onmousedown={startResizing}
				></div>
			{/if}
		</div>
	{/if}
</div>
