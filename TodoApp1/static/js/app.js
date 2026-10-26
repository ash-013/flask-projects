const list = document.getElementById('todo-list');
const form = document.getElementById('add-form');
const titleInput = document.getElementById('new-title');
const addBtn = document.getElementById('add-btn');
const messageBox = document.getElementById('message');
const footer = document.getElementById('footer');

// Local copy of the todos. The UI renders from this, so we don't
// need to re-fetch the whole list after every add/update/delete.
let todos = [];

async function api(url, options = {}) {
    const res = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
        ...options
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
        throw new Error(data.message || `Request failed (${res.status})`);
    }
    return data;
}

function showError(text) {
    messageBox.textContent = text;
    messageBox.className = 'message error';
}

function clearError() {
    messageBox.textContent = '';
    messageBox.className = 'message';
}

// ---------- Load & render ----------
async function loadTodos() {
    try {
        const data = await api('/todos');
        todos = data.todos;
        renderTodos();
        clearError();
    } catch (err) {
        showError(err.message);
    }
}

function renderTodos() {
    list.innerHTML = '';

    if (todos.length === 0) {
        list.innerHTML = '<li class="empty">No todos yet. Add one above!</li>';
        footer.textContent = '';
        return;
    }

    todos.forEach(todo => list.appendChild(createTodoItem(todo)));

    const remaining = todos.filter(t => !t.completed).length;
    footer.textContent = `${remaining} of ${todos.length} remaining`;
}

function createTodoItem(todo) {
    const li = document.createElement('li');
    li.className = 'todo-item' + (todo.completed ? ' completed' : '');

    // Checkbox -> PUT { completed }
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.checked = todo.completed;
    checkbox.addEventListener('change',
        () => updateTodo(todo.id, { completed: checkbox.checked }));

    // Title (textContent is used so user input is never treated as HTML)
    const title = document.createElement('span');
    title.className = 'todo-title';
    title.textContent = todo.title;

    const editBtn = document.createElement('button');
    editBtn.className = 'btn-small';
    editBtn.textContent = 'Edit';
    editBtn.addEventListener('click', () => startEditing(li, todo));

    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'btn-small btn-danger';
    deleteBtn.textContent = 'Delete';
    deleteBtn.addEventListener('click', () => deleteTodo(todo.id));

    li.append(checkbox, title, editBtn, deleteBtn);
    return li;
}

// ---------- Create ----------
// One request; the server returns the new todo, so we insert it locally.
form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const title = titleInput.value.trim();
    if (!title) {
        showError('Title cannot be empty');
        return;
    }

    addBtn.disabled = true;
    try {
        const data = await api('/todos', {
            method: 'POST',
            body: JSON.stringify({ title })
        });
        todos.unshift(data.todo); // server sorts by id desc, so newest goes first
        renderTodos();
        clearError();
        titleInput.value = '';
    } catch (err) {
        showError(err.message);
    } finally {
        addBtn.disabled = false;
        titleInput.focus();
    }
});

// ---------- Update ----------
// Optimistic: change the UI immediately, roll back only if the server fails.
async function updateTodo(id, changes) {
    const todo = todos.find(t => t.id === id);
    if (!todo) return;

    const backup = { ...todo };
    Object.assign(todo, changes);
    renderTodos();

    try {
        await api(`/todos/${id}`, {
            method: 'PUT',
            body: JSON.stringify(changes)
        });
        clearError();
    } catch (err) {
        Object.assign(todo, backup);
        renderTodos();
        showError(err.message);
    }
}

// Swaps the title for an input box. Enter saves, Escape cancels.
function startEditing(li, todo) {
    const titleSpan = li.querySelector('.todo-title');
    const input = document.createElement('input');
    input.type = 'text';
    input.className = 'edit-input';
    input.value = todo.title;
    input.maxLength = 255;

    titleSpan.replaceWith(input);
    input.focus();
    input.select();

    let finished = false;
    const finish = async (save) => {
        if (finished) return;
        finished = true;
        const newTitle = input.value.trim();
        if (save && newTitle && newTitle !== todo.title) {
            await updateTodo(todo.id, { title: newTitle });
        } else {
            if (save && !newTitle) showError('Title cannot be empty');
            renderTodos(); // just restore the view, no network call needed
        }
    };

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') finish(true);
        if (e.key === 'Escape') finish(false);
    });
    input.addEventListener('blur', () => finish(true));
}

// ---------- Delete ----------
// Optimistic: remove immediately, put it back if the server fails.
async function deleteTodo(id) {
    if (!confirm('Delete this todo?')) return;

    const index = todos.findIndex(t => t.id === id);
    if (index === -1) return;

    const [removed] = todos.splice(index, 1);
    renderTodos();

    try {
        await api(`/todos/${id}`, { method: 'DELETE' });
        clearError();
    } catch (err) {
        todos.splice(index, 0, removed);
        renderTodos();
        showError(err.message);
    }
}

// Load todos when the page opens
loadTodos();