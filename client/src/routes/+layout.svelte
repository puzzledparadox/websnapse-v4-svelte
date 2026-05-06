<script lang="ts">
	import '@xyflow/svelte/dist/style.css';
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import { SvelteFlowProvider } from '@xyflow/svelte';

	let { children } = $props();
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

<SvelteFlowProvider>
	{@render children()}
</SvelteFlowProvider>
