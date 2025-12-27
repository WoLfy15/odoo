// Calendar Logic - Full Implementation
// Uses date-fns for date manipulation

// State Management
let currentDate = new Date();
let globalTasks = [];
let selectedDate = null;
let technicians = [];

// Initialize Calendar
document.addEventListener('DOMContentLoaded', function() {
    loadTechnicians();
    loadTasks();
    renderCalendar();
    setupFormHandlers();
});

// Load technicians for dropdown
function loadTechnicians() {
    fetch('/api/technicians')
        .then(res => res.json())
        .then(data => {
            technicians = data.technicians || [];
            populateTechnicianDropdown();
        })
        .catch(err => {
            console.error('Error loading technicians:', err);
            // Fallback - add default values
            technicians = [];
        });
}

// Populate technician dropdown
function populateTechnicianDropdown() {
    const select = document.getElementById('technician');
    select.innerHTML = '<option value="">Select a technician</option>';
    
    technicians.forEach(tech => {
        const option = document.createElement('option');
        option.value = tech.id;
        option.textContent = tech.name;
        select.appendChild(option);
    });
}

// Load tasks from backend
function loadTasks() {
    fetch('/api/requests')
        .then(res => res.json())
        .then(data => {
            globalTasks = data.requests || [];
            renderCalendar();
        })
        .catch(err => {
            console.error('Error loading tasks:', err);
            globalTasks = [];
        });
}

// Render Calendar Grid
function renderCalendar() {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    // Update month/year display
    const monthNames = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ];
    document.getElementById('monthYear').textContent = `${monthNames[month]} ${year}`;
    
    // Get first day of month and number of days
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const daysInPrevMonth = new Date(year, month, 0).getDate();
    
    const calendarDays = document.getElementById('calendarDays');
    calendarDays.innerHTML = '';
    
    // Add days from previous month
    for (let i = firstDay - 1; i >= 0; i--) {
        const day = daysInPrevMonth - i;
        const cell = createDayCell(day, true, new Date(year, month - 1, day));
        calendarDays.appendChild(cell);
    }
    
    // Add days of current month
    const today = new Date();
    for (let day = 1; day <= daysInMonth; day++) {
        const cellDate = new Date(year, month, day);
        const isToday = isSameDay(cellDate, today);
        const cell = createDayCell(day, false, cellDate, isToday);
        calendarDays.appendChild(cell);
    }
    
    // Add days from next month
    const remainingCells = 42 - (firstDay + daysInMonth); // 6 rows × 7 days
    for (let day = 1; day <= remainingCells; day++) {
        const cell = createDayCell(day, true, new Date(year, month + 1, day));
        calendarDays.appendChild(cell);
    }
}

// Create individual day cell
function createDayCell(day, isOtherMonth, cellDate, isToday = false) {
    const cell = document.createElement('div');
    cell.className = 'day-cell';
    
    if (isOtherMonth) {
        cell.classList.add('other-month');
    }
    
    if (isToday) {
        cell.classList.add('today');
    }
    
    // Add click handler for current month days
    if (!isOtherMonth) {
        cell.addEventListener('click', () => openCreateModalForDate(cellDate));
    }
    
    // Day number
    const dayNumber = document.createElement('div');
    dayNumber.className = 'day-number';
    dayNumber.textContent = day;
    cell.appendChild(dayNumber);
    
    // Tasks container
    const tasksContainer = document.createElement('div');
    tasksContainer.className = 'day-tasks';
    
    // Filter and sort tasks for this day
    if (!isOtherMonth) {
        const dayTasks = globalTasks.filter(task => {
            const taskDate = new Date(task.scheduledDate || task.dueDate);
            return isSameDay(taskDate, cellDate);
        });
        
        // Sort: CORRECTIVE first, then PREVENTIVE
        dayTasks.sort((a, b) => {
            const aOrder = a.type === 'CORRECTIVE' ? 0 : 1;
            const bOrder = b.type === 'CORRECTIVE' ? 0 : 1;
            return aOrder - bOrder;
        });
        
        // Add task pills
        dayTasks.slice(0, 3).forEach(task => { // Show max 3 tasks
            const pill = document.createElement('div');
            pill.className = `task-pill ${task.type.toLowerCase()}`;
            pill.textContent = task.title;
            pill.title = `${task.title} (${task.status})`;
            tasksContainer.appendChild(pill);
        });
        
        // Show overflow indicator
        if (dayTasks.length > 3) {
            const overflow = document.createElement('div');
            overflow.className = 'task-pill';
            overflow.style.background = '#999';
            overflow.textContent = `+${dayTasks.length - 3} more`;
            tasksContainer.appendChild(overflow);
        }
    }
    
    cell.appendChild(tasksContainer);
    return cell;
}

// Date utility: Check if two dates are the same day
function isSameDay(date1, date2) {
    return date1.getFullYear() === date2.getFullYear() &&
           date1.getMonth() === date2.getMonth() &&
           date1.getDate() === date2.getDate();
}

// Format date to YYYY-MM-DD
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

// Navigation
function previousMonth() {
    currentDate.setMonth(currentDate.getMonth() - 1);
    renderCalendar();
}

function nextMonth() {
    currentDate.setMonth(currentDate.getMonth() + 1);
    renderCalendar();
}

// Modal Management
function openCreateModalForDate(date) {
    selectedDate = date;
    document.getElementById('selectedDate').value = formatDate(date);
    openCreateModal();
}

function openCreateModal() {
    if (selectedDate) {
        document.getElementById('selectedDate').value = formatDate(selectedDate);
    }
    document.getElementById('createRequestModal').classList.add('show');
    document.body.style.overflow = 'hidden';
}

function closeCreateModal() {
    document.getElementById('createRequestModal').classList.remove('show');
    document.getElementById('createRequestForm').reset();
    clearErrors();
    document.body.style.overflow = 'auto';
}

// Clear error messages
function clearErrors() {
    document.getElementById('subjectError').style.display = 'none';
    document.getElementById('technicianError').style.display = 'none';
}

// Form Validation and Submission
function setupFormHandlers() {
    document.getElementById('createRequestForm').addEventListener('submit', handleFormSubmit);
}

function handleFormSubmit(e) {
    e.preventDefault();
    
    clearErrors();
    
    // Get form values
    const subject = document.getElementById('subject').value.trim();
    const techniciandId = document.getElementById('technician').value;
    const description = document.getElementById('description').value.trim();
    const requestType = document.querySelector('input[name="requestType"]:checked').value;
    const dueDate = document.getElementById('dueDate').value;
    
    // Validation
    let isValid = true;
    
    if (!subject) {
        document.getElementById('subjectError').textContent = 'Subject is required';
        document.getElementById('subjectError').style.display = 'block';
        isValid = false;
    }
    
    if (!techniciandId) {
        document.getElementById('technicianError').textContent = 'Please select a technician';
        document.getElementById('technicianError').style.display = 'block';
        isValid = false;
    }
    
    if (!isValid) {
        return;
    }
    
    // Create request object
    const requestData = {
        title: subject,
        description: description,
        technician_id: parseInt(techniciandId),
        type: requestType,
        status: 'NEW_REQUEST',
        scheduled_date: document.getElementById('selectedDate').value,
        due_date: dueDate || null
    };
    
    // Send to backend
    fetch('/api/requests', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            showToast('Request Created Successfully!', 'success');
            closeCreateModal();
            loadTasks(); // Reload tasks and re-render calendar
        } else {
            showToast('Error: ' + (data.message || 'Failed to create request'), 'error');
        }
    })
    .catch(err => {
        console.error('Error creating request:', err);
        showToast('Error creating request', 'error');
    });
}

// Toast Notification
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Close modal when clicking outside
window.addEventListener('click', (e) => {
    const modal = document.getElementById('createRequestModal');
    if (e.target === modal) {
        closeCreateModal();
    }
});
