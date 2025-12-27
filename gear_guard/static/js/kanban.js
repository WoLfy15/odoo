// Technician Workspace Kanban Logic

// Utility: calculateTaskState(task)
function calculateTaskState(task) {
	const now = new Date();
	const due = task.dueDate ? new Date(task.dueDate) : null;
	const isOverdue = !!(due && now > due);
	const finished = task.status === 'REQUIRED' || task.status === 'SCRAP';
	const showWarning = isOverdue && !finished;
	return { isOverdue, showWarning };
}

// Render helpers
function cardBorderColor(task) {
	if (task.type === 'CORRECTIVE') return '#F97316';
	if (task.type === 'PREVENTIVE') return '#A855F7';
	return '#e5e7eb';
}

function typeBadgeClass(task) {
	return task.type === 'CORRECTIVE' ? 'badge orange' : 'badge purple';
}

// Simple store
const store = {
	tasks: (window.KANBAN_DATA && window.KANBAN_DATA.tasks) ? window.KANBAN_DATA.tasks.slice() : [],
	moveTask(id, newStatus) {
		const t = this.tasks.find(x => x.id === id);
		if (!t) return;
		t.status = newStatus; // optimistic update
		// persist to server
		fetch('/kanban/move', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ taskId: id, newStatus })
		}).catch(() => {/* ignore for now */});
		render();
	}
};

// Drag & Drop setup
let dragState = { draggingId: null };

function makeDraggable(cardEl, task) {
	cardEl.draggable = true;
	cardEl.addEventListener('dragstart', () => {
		dragState.draggingId = task.id;
		cardEl.classList.add('dragging');
	});
	cardEl.addEventListener('dragend', (ev) => {
		cardEl.classList.remove('dragging');
		onDragEnd(ev);
	});
}

function setupDroppable(containerEl) {
	containerEl.addEventListener('dragover', (ev) => {
		ev.preventDefault();
	});
	containerEl.addEventListener('drop', (ev) => {
		ev.preventDefault();
		const column = containerEl.closest('.kanban-column');
		const containerID = column ? column.getAttribute('data-status') : null;
		if (!containerID) return;
		if (!dragState.draggingId) return;
		store.moveTask(dragState.draggingId, containerID);
		dragState.draggingId = null;
	});
}

// onDragEnd logic
function onDragEnd(ev) {
	// If dropped outside a container, do nothing.
	// We rely on drop handlers to perform status updates.
}

// Render board
function render() {
	const columns = document.querySelectorAll('.kanban-column');
	const byStatus = { NEW: [], NEW_REQUEST: [], IN_PROGRESS: [], REQUIRED: [], SCRAP: [], UNDER_REVIEW: [] };
	store.tasks.forEach(t => {
		if (!byStatus[t.status]) byStatus[t.status] = [];
		byStatus[t.status].push(t);
	});

	columns.forEach(col => {
		const status = col.getAttribute('data-status');
		const body = col.querySelector('.kanban-column-body');
		body.innerHTML = '';
		(byStatus[status] || []).forEach(task => {
			const state = calculateTaskState(task);
			const card = document.createElement('div');
			card.className = 'kanban-card';
			card.style.borderLeftColor = cardBorderColor(task);
			card.innerHTML = `
				<div>
					<span class="${typeBadgeClass(task)}">${task.type}</span>
					<strong>${task.title}</strong>
				</div>
				<div style="font-size:12px;color:#666;margin-top:6px;">
					Due: <strong>${task.dueDate || '-'}</strong>
				</div>
				${state.showWarning ? '<div class="warning">⚠ Overdue</div>' : ''}
			`;
			makeDraggable(card, task);
			body.appendChild(card);
		});
		setupDroppable(body);
	});
}

document.addEventListener('DOMContentLoaded', render);

// Expose for debugging
window.KANBAN = { store, calculateTaskState };
