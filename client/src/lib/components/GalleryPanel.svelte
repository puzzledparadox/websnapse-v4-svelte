<script lang="ts">
	import { GALLERY_SYSTEMS, GALLERY_CATEGORIES, type GallerySystem } from '$lib/constants/gallery';
	import { Search, Zap, Calculator, GitCompare, Layout, ChevronRight } from 'lucide-svelte';
	import Katex from 'svelte-katex';
	import 'katex/dist/katex.min.css';

	let { onSelect } = $props<{ onSelect: (system: GallerySystem) => void }>();

	let searchQuery = $state('');
	let activeCategory = $state('all');
	let expandedId = $state<string | null>(null);

	const categoryIcons: Record<string, any> = {
		all: Layout,
		generators: Zap,
		arithmetic: Calculator,
		comparators: GitCompare,
	};

	let filteredSystems = $derived.by(() => {
		let systems = GALLERY_SYSTEMS;

		if (activeCategory !== 'all') {
			systems = systems.filter(s => s.category === activeCategory);
		}

		if (searchQuery.trim()) {
			const q = searchQuery.toLowerCase();
			systems = systems.filter(
				s =>
					s.title.toLowerCase().includes(q) ||
					s.description.toLowerCase().includes(q) ||
					s.category.toLowerCase().includes(q)
			);
		}

		return systems;
	});

	function handleSelect(system: GallerySystem) {
		onSelect(system);
	}
</script>

<div class="gallery-panel flex flex-col gap-3">
	<!-- Search -->
	<div class="relative">
		<Search size={14} class="absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-400" />
		<input
			type="text"
			placeholder="Search systems..."
			bind:value={searchQuery}
			class="w-full rounded-lg border border-gray-200 bg-gray-50 py-2 pl-8 pr-3 text-xs text-gray-700 transition-colors placeholder:text-gray-400 focus:border-purple-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-purple-100"
		/>
	</div>

	<!-- Category pills -->
	<div class="flex flex-wrap gap-1.5">
		{#each GALLERY_CATEGORIES as cat}
			{@const Icon = categoryIcons[cat.id]}
			<button
				onclick={() => activeCategory = cat.id}
				class="flex items-center gap-1 rounded-full border px-2.5 py-1 text-[11px] font-semibold transition-all duration-200
					{activeCategory === cat.id
						? 'border-purple-400 bg-purple-50 text-purple-700 shadow-sm'
						: 'border-gray-200 bg-white text-gray-500 hover:border-gray-300 hover:bg-gray-50 hover:text-gray-700'}"
			>
				<Icon size={12} />
				{cat.label}
			</button>
		{/each}
	</div>

	<!-- System cards -->
	<div class="flex flex-col gap-2">
		{#if filteredSystems.length === 0}
			<p class="py-4 text-center text-xs italic text-gray-400">No systems match your search.</p>
		{:else}
			{#each filteredSystems as system (system.id)}
				{@const isExpanded = expandedId === system.id}
				{@const Icon = categoryIcons[system.category] ?? Layout}
				<div
					class="group gallery-card overflow-hidden rounded-lg border transition-all duration-200
						{isExpanded
							? 'border-purple-300 bg-purple-50/50 shadow-md'
							: 'border-gray-200 bg-white hover:border-purple-200 hover:shadow-sm'}"
				>
					<!-- Header row (clickable to expand/collapse) -->
					<button
						class="flex w-full items-center gap-2.5 px-3 py-2.5 text-left"
						onclick={() => expandedId = isExpanded ? null : system.id}
					>
						<div
							class="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-md transition-colors
								{isExpanded ? 'bg-purple-200 text-purple-700' : 'bg-gray-100 text-gray-500 group-hover:bg-purple-100 group-hover:text-purple-600'}"
						>
							<Icon size={14} />
						</div>
						<div class="min-w-0 flex-1">
							<div class="truncate text-xs font-bold text-gray-800">{system.title}</div>
							<div class="truncate text-[10px] text-gray-500">{system.nodes.length} neurons · {system.edges.length} synapses</div>
						</div>
						<ChevronRight
							size={14}
							class="flex-shrink-0 text-gray-400 transition-transform duration-200
								{isExpanded ? 'rotate-90 text-purple-500' : ''}"
						/>
					</button>

					<!-- Expanded details -->
					{#if isExpanded}
						<div class="border-t border-purple-200/60 px-3 pb-3 pt-2">
							<p class="mb-3 text-[11px] leading-relaxed text-gray-600">{system.description}</p>

							<!-- Mini topology preview -->
							<div class="mb-3 flex flex-wrap gap-1">
								{#each system.nodes as node}
									{@const nt = node.data.neuronType}
									<span
										class="inline-flex items-center rounded-full border px-1.5 py-0.5 text-[9px] font-bold tracking-wide
											{nt === 'input'
												? 'border-emerald-200 bg-emerald-50 text-emerald-700'
												: nt === 'output'
													? 'border-amber-200 bg-amber-50 text-amber-700'
													: 'border-slate-200 bg-slate-50 text-slate-600'}"
									>
										<Katex>{node.data.id}</Katex>
									</span>
								{/each}
							</div>

							<button
								onclick={() => handleSelect(system)}
								class="flex w-full items-center justify-center gap-1.5 rounded-md bg-purple-600 px-3 py-2 text-xs font-bold text-white shadow-sm transition-all duration-200 hover:bg-purple-700 hover:shadow active:scale-[0.98]"
							>
								<Zap size={12} />
								Load System
							</button>
						</div>
					{/if}
				</div>
			{/each}
		{/if}
	</div>
</div>
