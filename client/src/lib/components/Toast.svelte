<!--
	@component
	Toast.svelte
	
	A global toast notification system. It exports a module-level `showToast`
	function that can be called from anywhere in the app to display temporary,
	stacking alert messages (success, error, info) in the bottom right corner.
-->
<script lang="ts" module>
	import { CheckCircle, AlertCircle, Info, X } from 'lucide-svelte';

	interface ToastItem {
		id: number;
		message: string;
		type: 'success' | 'error' | 'info';
		duration?: number;
	}

	// Shared reactive state — lives at module level so it persists across component instances
	let toasts = $state<ToastItem[]>([]);
	let nextId = 0;

	/**
	 * Pushes a new toast notification onto the screen.
	 * 
	 * @param message - The text content of the toast.
	 * @param type - The visual style ('success', 'error', 'info'). Defaults to 'success'.
	 * @param duration - Time in milliseconds before the toast auto-dismisses. Defaults to 3000ms.
	 */
	export function showToast(message: string, type: ToastItem['type'] = 'success', duration = 3000) {
		const id = nextId++;
		toasts = [...toasts, { id, message, type, duration }];

		if (duration > 0) {
			setTimeout(() => {
				toasts = toasts.filter(t => t.id !== id);
			}, duration);
		}
	}
</script>

<script lang="ts">
	/**
	 * Manually removes a toast notification by its ID.
	 * 
	 * @param id - The unique identifier of the toast to remove.
	 */
	function dismiss(id: number) {
		toasts = toasts.filter(t => t.id !== id);
	}

	const icons = { success: CheckCircle, error: AlertCircle, info: Info };
	const colors = {
		success: 'border-emerald-300 bg-emerald-50 text-emerald-800',
		error: 'border-red-300 bg-red-50 text-red-800',
		info: 'border-blue-300 bg-blue-50 text-blue-800'
	};
	const iconColors = {
		success: 'text-emerald-500',
		error: 'text-red-500',
		info: 'text-blue-500'
	};
</script>

{#if toasts.length > 0}
	<div class="fixed bottom-6 right-6 z-[200] flex flex-col-reverse gap-2">
		{#each toasts as toast (toast.id)}
			{@const Icon = icons[toast.type]}
			<div
				class="toast-enter flex min-w-[280px] max-w-sm items-center gap-3 rounded-lg border px-4 py-3 shadow-lg backdrop-blur-sm {colors[toast.type]}"
			>
				<Icon size={18} class="flex-shrink-0 {iconColors[toast.type]}" />
				<span class="flex-1 text-sm font-medium">{toast.message}</span>
				<button
					onclick={() => dismiss(toast.id)}
					class="flex-shrink-0 rounded p-0.5 opacity-60 transition-opacity hover:opacity-100"
				>
					<X size={14} />
				</button>
			</div>
		{/each}
	</div>
{/if}

<style>
	@keyframes toast-slide-in {
		from {
			opacity: 0;
			transform: translateX(100%) scale(0.95);
		}
		to {
			opacity: 1;
			transform: translateX(0) scale(1);
		}
	}

	.toast-enter {
		animation: toast-slide-in 0.35s cubic-bezier(0.16, 1, 0.3, 1);
	}
</style>
