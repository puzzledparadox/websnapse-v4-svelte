import type { Node, Edge } from '@xyflow/svelte';
import type { AppNode } from './workspace.svelte';

export class UIState {
	// Sidebar State
	sidebarOpen = $state(true);
	sidebarWidth = $state(384);
	isResizingSidebar = $state(false);
	galleryHeight = $state(300);
	openSections = $state({
		persistence: true,
		gallery: true,
		config: true,
		judging: true,
		configGraph: true
	});

	// Context Menu State
	contextMenuState = $state({
		show: false,
		x: 0,
		y: 0,
		options: [] as any[]
	});

	// Modals State
	showClearModal = $state(false);
	showNodeModal = $state(false);
	showConfigGraphModal = $state(false);

	// Node Edit/Create State
	pendingNodePosition = $state({ x: 0, y: 0 });
	defaultNodeId = $state('');
	editTargetNode = $state<AppNode | null>(null);

	// Event Handlers for UI Elements
	handleSidebarResizeStart() {
		this.isResizingSidebar = true;
		document.body.style.cursor = 'col-resize';
		document.body.style.userSelect = 'none';
	}

	handleSidebarResizeMove(e: MouseEvent) {
		if (this.isResizingSidebar) {
			this.sidebarWidth = Math.max(280, Math.min(600, e.clientX));
		}
	}

	handleSidebarResizeEnd() {
		if (this.isResizingSidebar) {
			this.isResizingSidebar = false;
			document.body.style.cursor = '';
			document.body.style.userSelect = 'auto';
		}
	}

	showContextMenu(event: MouseEvent, options: any[]) {
		event.preventDefault();
		event.stopPropagation();
		this.contextMenuState = {
			show: true,
			x: event.clientX,
			y: event.clientY,
			options
		};
	}

	closeContextMenu() {
		this.contextMenuState.show = false;
	}
}

export const uiState = new UIState();
