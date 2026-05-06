<script lang="ts">
	let { show = $bindable(false), onSubmit, onCancel, defaultId = '', initialNode = null } = $props();

	let nodeId = $state('');
	let nodeType = $state('regular');
	let content = $state('0'); // spikes
	let rules = $state(['a/a \\to a; 0']);

	let isEditMode = $derived(!!initialNode);

	function handleAddRule() {
		rules.push('a/a \\to a; 0');
	}

	function handleCreate() {
		onSubmit({
			id: nodeId || defaultId,
			type: nodeType,
			spikes: nodeType === 'regular' ? (parseInt(content, 10) || 0) : (nodeType === 'input' ? content : ''),
			rules: nodeType === 'regular' ? rules.filter(r => r.trim() !== '') : [],
			isEdit: isEditMode
		});
		show = false;
	}

	function handleCancel() {
		if (onCancel) onCancel();
		show = false;
	}
	
	// Reset state when modal opens
	$effect(() => {
		if (show) {
			if (initialNode) {
				nodeId = initialNode.data.id;
				nodeType = initialNode.data.neuronType;
				content = String(initialNode.data.spikes);
				rules = initialNode.data.rules ? [...initialNode.data.rules] : [];
			} else {
				nodeId = defaultId;
				nodeType = 'regular';
				content = '0';
				rules = ['a/a \\to a; 0'];
			}
		}
	});
</script>

{#if show}
<!-- Backdrop -->
<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div 
	class="absolute inset-0 z-[100] flex items-center justify-center bg-black/20 backdrop-blur-sm"
	onclick={handleCancel}
>
	<!-- Modal -->
	<div 
		class="w-80 rounded-xl bg-white p-6 shadow-xl"
		onclick={(e) => e.stopPropagation()}
	>
		<h2 class="mb-4 text-xl font-bold text-slate-800">{isEditMode ? 'Edit Node' : 'Node Properties'}</h2>

		<!-- ID Input -->
		<div class="mb-4">
			<label for="nodeId" class="mb-1 block text-sm font-semibold text-slate-700">ID</label>
			<input
				id="nodeId"
				type="text"
				bind:value={nodeId}
				class="w-full rounded-lg border border-slate-300 p-2.5 font-serif text-slate-700 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
			/>
		</div>

		<!-- Type Select -->
		<div class="mb-4">
			<label for="nodeType" class="mb-1 block text-sm font-semibold text-slate-700">Type</label>
			<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
			<div class="relative">
				<select
					id="nodeType"
					bind:value={nodeType}
					class="w-full appearance-none rounded-lg border border-slate-300 bg-white p-2.5 text-slate-700 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
				>
					<option value="regular">regular</option>
					<option value="input">input</option>
					<option value="output">output</option>
				</select>
				<div class="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-700">
					<svg class="h-4 w-4 fill-current" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M9.293 12.95l.707.707L15.657 8l-1.414-1.414L10 10.828 5.757 6.586 4.343 8z"/></svg>
				</div>
			</div>
		</div>

		<!-- Content (Spikes) Input -->
		{#if nodeType === 'regular'}
			<div class="mb-4">
				<label for="content" class="mb-1 block text-sm font-semibold text-slate-700">Spikes</label>
				<input
					id="content"
					type="number"
					bind:value={content}
					min="0"
					class="w-full rounded-lg border border-blue-400 p-2.5 text-slate-700 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
				/>
			</div>
		{:else if nodeType === 'input'}
			<div class="mb-4">
				<label for="content" class="mb-1 block text-sm font-semibold text-slate-700">Spike Train</label>
				<input
					id="content"
					type="text"
					bind:value={content}
					placeholder="e.g. 1111011"
					class="w-full rounded-lg border border-blue-400 p-2.5 font-mono text-slate-700 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
				/>
			</div>
		{/if}

		<!-- Rules -->
		{#if nodeType === 'regular'}
			<div class="mb-6">
				<span class="mb-1 block text-sm font-semibold text-slate-700">Rules</span>
				{#each rules as rule, i}
					<div class="mb-2 flex items-center gap-2">
						<input
							type="text"
							bind:value={rules[i]}
							class="w-full rounded-lg border border-slate-300 p-2.5 font-mono text-sm text-slate-700 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
						/>
						<button
							class="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-slate-200 text-red-500 hover:bg-red-50 hover:text-red-700"
							onclick={() => { rules = rules.filter((_, index) => index !== i); }}
							title="Remove Rule"
						>
							&times;
						</button>
					</div>
				{/each}
				
				<button
					class="w-full rounded-lg border-2 border-dashed border-slate-200 py-2.5 text-sm font-semibold text-slate-400 transition-colors hover:border-blue-300 hover:text-blue-500"
					onclick={handleAddRule}
				>
					Add Rule
				</button>
			</div>
		{/if}

		<!-- Create Button -->
		<button
			class="w-full rounded-lg bg-blue-100 py-2.5 font-bold text-blue-800 transition-colors hover:bg-blue-200"
			onclick={handleCreate}
		>
			{isEditMode ? 'Save Changes' : 'Create'}
		</button>
	</div>
</div>
{/if}
