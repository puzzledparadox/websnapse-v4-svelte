<script lang="ts">
	import { onMount } from 'svelte';
	
	let { x = 0, y = 0, show = false, options = [], onClose } = $props();

	let menuElement: HTMLDivElement | null = $state(null);
	let adjustedX = $state(0);
	let adjustedY = $state(0);

	$effect(() => {
		if (show && menuElement) {
			// Adjust position to stay within viewport
			const rect = menuElement.getBoundingClientRect();
			const vw = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
			const vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);
			
			if (x + rect.width > vw) {
				adjustedX = x - rect.width;
			} else {
				adjustedX = x;
			}
			
			if (y + rect.height > vh) {
				adjustedY = y - rect.height;
			} else {
				adjustedY = y;
			}
		}
	});

	function handleClickOutside(event: MouseEvent) {
		if (show && menuElement && !menuElement.contains(event.target as Node)) {
			// Wait a tick to allow other click events to resolve (like SvelteFlow's built-ins)
			setTimeout(() => {
				onClose();
			}, 10);
		}
	}

	onMount(() => {
		document.addEventListener('click', handleClickOutside);
		document.addEventListener('contextmenu', handleClickOutside);
		return () => {
			document.removeEventListener('click', handleClickOutside);
			document.removeEventListener('contextmenu', handleClickOutside);
		};
	});
</script>

{#if show}
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		bind:this={menuElement}
		class="fixed z-[200] min-w-[180px] rounded-lg border border-slate-200 bg-white py-2 shadow-xl"
		style="left: {adjustedX}px; top: {adjustedY}px;"
		oncontextmenu={(e) => { e.preventDefault(); e.stopPropagation(); }}
		onclick={(e) => e.stopPropagation()}
	>
		{#each options as option}
			{#if option.divider}
				<div class="my-1.5 border-t border-slate-100"></div>
			{:else}
				<button
					class="flex w-full items-center gap-3 px-4 py-2 text-left text-sm font-semibold text-slate-800 transition-colors hover:bg-slate-100 hover:text-purple-700"
					onclick={(e) => {
						e.preventDefault();
						e.stopPropagation();
						option.action();
						onClose();
					}}
				>
					{#if option.icon}
						<option.icon size={16} class="shrink-0 text-slate-600" />
					{/if}
					{option.label}
				</button>
			{/if}
		{/each}
	</div>
{/if}
