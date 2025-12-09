const input = document.getElementById('taskInput');
const addBtn = document.getElementById('addTaskButton');
const suggestBtn = document.getElementById('suggestBtn');
const taskList = document.getElementById('taskList');
const aiResult = document.getElementById('aiResult');
const logoutBtn = document.getElementById('logoutBtn');
const userEmailSpan = document.getElementById('userEmail');
const taskPlan = document.getElementById('taskPlan');

// New input fields
const prioritySelect = document.getElementById('prioritySelect');
const categorySelect = document.getElementById('categorySelect');
const dueDateInput = document.getElementById('dueDateInput');
const timeEstimate = document.getElementById('timeEstimate');
const importanceSelect = document.getElementById('importanceSelect');

let tasks = [];
let reviews = [];
let currentReviewIndex = 0;
let selectedRating = 0;

// Check authentication on load
async function checkAuth() {
  try {
    const response = await fetch('http://127.0.0.1:5000/check-auth', {
      credentials: 'include'
    });
    const data = await response.json();
    
    if (!data.authenticated) {
      window.location.href = 'login.html';
      return false;
    }
    
    userEmailSpan.textContent = data.email;
    
    // Show admin link if user is admin
    if (data.is_admin) {
      document.getElementById('adminLink').style.display = 'inline';
      document.getElementById('adminLink').href = 'admin.html';
    }
    
    return true;
  } catch (error) {
    console.error('Auth check failed:', error);
    window.location.href = 'login.html';
    return false;
  }
}

// Logout handler
logoutBtn.onclick = async () => {
  try {
    await fetch('http://127.0.0.1:5000/logout', {
      method: 'POST',
      credentials: 'include'
    });
    localStorage.clear();
    window.location.href = 'login.html';
  } catch (error) {
    console.error('Logout failed:', error);
  }
};

// Load tasks from server
async function loadTasks() {
  try {
    const response = await fetch('http://127.0.0.1:5000/tasks', {
      credentials: 'include'
    });
    const data = await response.json();
    tasks = data.tasks;
    render();
  } catch (error) {
    console.error('Error loading tasks:', error);
  }
}

// Update statistics
function updateStats() {
  const total = tasks.length;
  const completed = tasks.filter(t => t.completed).length;
  const pending = total - completed;
  
  document.getElementById('totalTasks').textContent = total;
  document.getElementById('completedTasks').textContent = completed;
  document.getElementById('pendingTasks').textContent = pending;
}

addBtn.onclick = async () => {
  const task = input.value.trim();
  if(!task) return alert("Please enter a task!");
  
  // Optimistic UI update - add task immediately
  const tempTask = {
    id: Date.now(), // temporary ID
    text: task,
    priority: prioritySelect.value,
    category: categorySelect.value,
    due_date: dueDateInput.value || null,
    estimated_time: parseInt(timeEstimate.value),
    importance: parseInt(importanceSelect.value),
    completed: false
  };
  
  tasks.push(tempTask);
  render();
  
  // Clear inputs immediately
  input.value = "";
  dueDateInput.value = "";
  
  try {
    const response = await fetch('http://127.0.0.1:5000/add-task', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      credentials: 'include',
      body: JSON.stringify({
        text: task,
        priority: prioritySelect.value,
        category: categorySelect.value,
        due_date: dueDateInput.value || null,
        estimated_time: parseInt(timeEstimate.value),
        importance: parseInt(importanceSelect.value)
      })
    });
    
    const data = await response.json();
    if (data.success) {
      // Replace temp task with real task from server
      await loadTasks();
    } else {
      // Revert optimistic update on error
      tasks = tasks.filter(t => t.id !== tempTask.id);
      render();
      alert('Error adding task: ' + data.message);
    }
  } catch (error) {
    console.error('Error adding task:', error);
    // Revert optimistic update on error
    tasks = tasks.filter(t => t.id !== tempTask.id);
    render();
    alert('Failed to add task. Please try again.');
  }
};

// Allow Enter key to add task
input.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    addBtn.click();
  }
});

function render() {
  taskList.innerHTML = "";
  tasks.forEach((task, index) => {
    const li = document.createElement('li');
    li.className = 'fade-in'; // Add animation class
    if (task.completed) {
      li.classList.add('completed');
    }
    
    // Task header
    const taskHeader = document.createElement('div');
    taskHeader.className = 'task-header';
    
    const taskInfo = document.createElement('div');
    taskInfo.className = 'task-info';
    
    const taskText = document.createElement('div');
    taskText.className = 'task-text';
    taskText.innerText = task.text;
    
    // Task badges
    const badges = document.createElement('div');
    badges.className = 'task-badges';
    
    // Priority badge
    const priorityBadge = document.createElement('span');
    priorityBadge.className = `badge badge-${task.priority}`;
    const priorityEmojis = {urgent: '🔴', high: '🟠', medium: '🟡', low: '🟢'};
    priorityBadge.textContent = `${priorityEmojis[task.priority]} ${task.priority.toUpperCase()}`;
    badges.appendChild(priorityBadge);
    
    // Category badge
    if (task.category !== 'general') {
      const categoryBadge = document.createElement('span');
      categoryBadge.className = 'badge badge-category';
      const categoryEmojis = {work: '💼', personal: '👤', health: '❤️', finance: '💰', learning: '📚'};
      categoryBadge.textContent = `${categoryEmojis[task.category] || '📋'} ${task.category}`;
      badges.appendChild(categoryBadge);
    }
    
    // Time estimate badge
    const timeBadge = document.createElement('span');
    timeBadge.className = 'badge badge-time';
    timeBadge.textContent = `⏱️ ${task.estimated_time} min`;
    badges.appendChild(timeBadge);
    
    // Due date badge
    if (task.due_date) {
      const dueBadge = document.createElement('span');
      dueBadge.className = 'badge badge-due';
      const dueDate = new Date(task.due_date);
      const today = new Date();
      const daysUntil = Math.ceil((dueDate - today) / (1000 * 60 * 60 * 24));
      
      if (daysUntil < 0) {
        dueBadge.textContent = `⚠️ OVERDUE`;
        dueBadge.style.background = '#dc3545';
        dueBadge.style.color = 'white';
      } else if (daysUntil === 0) {
        dueBadge.textContent = `📅 Today`;
      } else if (daysUntil === 1) {
        dueBadge.textContent = `📅 Tomorrow`;
      } else {
        dueBadge.textContent = `📅 ${daysUntil} days`;
      }
      badges.appendChild(dueBadge);
    }
    
    taskInfo.appendChild(taskText);
    taskInfo.appendChild(badges);
    
    const actions = document.createElement('div');
    actions.className = 'task-actions';
    
    const completeBtn = document.createElement('button');
    completeBtn.className = 'complete-btn';
    completeBtn.textContent = task.completed ? '↺ Undo' : '✓ Done';
    completeBtn.onclick = () => toggleComplete(task.id);
    
    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'delete-btn';
    deleteBtn.textContent = '✕ Delete';
    deleteBtn.onclick = () => deleteTask(task.id);
    
    actions.appendChild(completeBtn);
    actions.appendChild(deleteBtn);
    
    taskHeader.appendChild(taskInfo);
    taskHeader.appendChild(actions);
    
    li.appendChild(taskHeader);
    taskList.appendChild(li);
  });
  
  updateStats();
}

async function toggleComplete(taskId) {
  // Optimistic UI update - toggle immediately
  const task = tasks.find(t => t.id === taskId);
  if (!task) return;
  
  const previousState = task.completed;
  task.completed = !task.completed;
  render();
  
  try {
    const response = await fetch(`http://127.0.0.1:5000/task/${taskId}/complete`, {
      method: 'PUT',
      credentials: 'include'
    });
    
    if (response.ok) {
      // Reload to ensure consistency
      await loadTasks();
    } else {
      // Revert on error
      task.completed = previousState;
      render();
      alert('Failed to update task. Please try again.');
    }
  } catch (error) {
    console.error('Error toggling task:', error);
    // Revert on error
    task.completed = previousState;
    render();
    alert('Failed to update task. Please try again.');
  }
}

async function deleteTask(taskId) {
  if (!confirm('Are you sure you want to delete this task?')) return;
  
  // Optimistic UI update - remove immediately
  const taskIndex = tasks.findIndex(t => t.id === taskId);
  if (taskIndex === -1) return;
  
  const deletedTask = tasks[taskIndex];
  tasks.splice(taskIndex, 1);
  render();
  
  try {
    const response = await fetch(`http://127.0.0.1:5000/task/${taskId}`, {
      method: 'DELETE',
      credentials: 'include'
    });
    
    if (response.ok) {
      // Reload to ensure consistency
      await loadTasks();
    } else {
      // Revert on error
      tasks.splice(taskIndex, 0, deletedTask);
      render();
      alert('Failed to delete task. Please try again.');
    }
  } catch (error) {
    console.error('Error deleting task:', error);
    // Revert on error
    tasks.splice(taskIndex, 0, deletedTask);
    render();
    alert('Failed to delete task. Please try again.');
  }
}

suggestBtn.onclick = async () => {
  const pendingTasks = tasks.filter(t => !t.completed);
  
  if(pendingTasks.length === 0) return alert("Add some tasks first!");
  
  aiResult.innerText = "🤔 AI is analyzing your tasks...";
  aiResult.style.display = 'flex';
  taskPlan.classList.remove('show');
  
  try{
    const resp = await fetch('http://127.0.0.1:5000/suggest', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      credentials: 'include',
      body: JSON.stringify({})
    });
    const data = await resp.json();
    
    // Show main suggestion
    aiResult.innerText = "💡 " + data.suggestion;
    
    // Show ordered task plan
    if (data.ordered_tasks && data.ordered_tasks.length > 0) {
      taskPlan.innerHTML = `
        <h3>📊 Your Optimized Task Plan</h3>
        <p style="color: #666; margin-bottom: 15px;">
          ${data.total_pending} pending tasks • ${Math.round(data.total_time_needed / 60)} hours estimated
        </p>
      `;
      
      data.ordered_tasks.forEach(item => {
        const taskDiv = document.createElement('div');
        taskDiv.className = 'planned-task';
        
        const priorityColors = {urgent: '#dc3545', high: '#fd7e14', medium: '#0984e3', low: '#6c757d'};
        taskDiv.style.borderLeftColor = priorityColors[item.priority] || '#667eea';
        
        taskDiv.innerHTML = `
          <span class="rank">${item.rank}</span>
          <strong>${item.text}</strong>
          <div class="reason">${item.reasons.join(' • ') || 'Standard priority'}</div>
        `;
        taskPlan.appendChild(taskDiv);
      });
      
      taskPlan.classList.add('show');
    }
  } catch(err) {
    aiResult.innerText = "❌ Error: " + err.message;
  }
};

// Initialize app
async function init() {
  const authenticated = await checkAuth();
  if (authenticated) {
    await loadTasks();
    await loadReviews();
    
    // Auto-refresh every 30 seconds to keep data in sync
    setInterval(async () => {
      try {
        await loadTasks();
      } catch (error) {
        console.error('Auto-refresh failed:', error);
      }
    }, 30000); // 30 seconds
    
    // Rotate reviews every 5 seconds
    setInterval(rotateReview, 5000);
  }
}

// Load reviews
async function loadReviews() {
  try {
    const response = await fetch('http://127.0.0.1:5000/reviews');
    const data = await response.json();
    reviews = data.reviews;
    if (reviews.length > 0) {
      displayReview(0);
    }
  } catch (error) {
    console.error('Failed to load reviews:', error);
  }
}

// Display a review
function displayReview(index) {
  if (reviews.length === 0) return;
  
  const review = reviews[index];
  const stars = '★'.repeat(review.rating) + '☆'.repeat(5 - review.rating);
  
  document.getElementById('reviewContent').innerHTML = `
    <div style="color: #ffc107; font-size: 24px; margin-bottom: 10px;">${stars}</div>
    <p style="font-style: italic; color: #666; margin-bottom: 10px;">"${review.text || 'Great app!'}"</p>
    <small style="color: #999;">- ${review.user_email}</small>
  `;
}

// Rotate to next review
function rotateReview() {
  if (reviews.length === 0) return;
  currentReviewIndex = (currentReviewIndex + 1) % reviews.length;
  displayReview(currentReviewIndex);
}

// Review form handlers
document.getElementById('showReviewForm').onclick = () => {
  document.getElementById('reviewForm').style.display = 'block';
  document.getElementById('showReviewForm').style.display = 'none';
};

document.getElementById('cancelReview').onclick = () => {
  document.getElementById('reviewForm').style.display = 'none';
  document.getElementById('showReviewForm').style.display = 'inline-block';
  selectedRating = 0;
  updateStars();
  document.getElementById('reviewText').value = '';
};

// Star rating
document.querySelectorAll('.star').forEach(star => {
  star.addEventListener('click', function() {
    selectedRating = parseInt(this.dataset.rating);
    updateStars();
  });
  
  star.addEventListener('mouseenter', function() {
    const rating = parseInt(this.dataset.rating);
    highlightStars(rating);
  });
  
  star.addEventListener('mouseleave', function() {
    updateStars();
  });
});

function updateStars() {
  document.querySelectorAll('.star').forEach(star => {
    const rating = parseInt(star.dataset.rating);
    star.style.color = rating <= selectedRating ? '#ffc107' : '#ddd';
  });
}

function highlightStars(rating) {
  document.querySelectorAll('.star').forEach(star => {
    const starRating = parseInt(star.dataset.rating);
    star.style.color = starRating <= rating ? '#ffc107' : '#ddd';
  });
}

// Submit review
document.getElementById('submitReview').onclick = async () => {
  if (selectedRating === 0) {
    return alert('Please select a star rating!');
  }
  
  const text = document.getElementById('reviewText').value.trim();
  
  try {
    const response = await fetch('http://127.0.0.1:5000/add-review', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      credentials: 'include',
      body: JSON.stringify({
        rating: selectedRating,
        text: text
      })
    });
    
    const data = await response.json();
    
    if (data.success) {
      alert('✅ ' + data.message);
      document.getElementById('reviewForm').style.display = 'none';
      document.getElementById('showReviewForm').style.display = 'none';
      selectedRating = 0;
      updateStars();
      document.getElementById('reviewText').value = '';
      await loadReviews();
    } else {
      alert('❌ ' + data.message);
    }
  } catch (error) {
    console.error('Failed to submit review:', error);
    alert('Failed to submit review. Please try again.');
  }
};

init();
