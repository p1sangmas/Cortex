// Modern Notification Panel Functionality

// Global notification array
let notifications = [];
let maxNotifications = 50; // Maximum number of notifications to keep

// Initialize notification panel
function initNotificationPanel() {
    const toggleBtn = document.getElementById('notifications-toggle');
    const panel = document.getElementById('notifications-panel');
    const clearBtn = document.getElementById('clear-notifications');
    
    // Toggle notification panel with smooth animation
    toggleBtn.addEventListener('click', () => {
        panel.classList.toggle('visible');
        
        // Reset notification counter when opened
        if (panel.classList.contains('visible')) {
            resetNotificationCounter();
        }
    });
    
    // Clear all notifications
    clearBtn.addEventListener('click', () => {
        clearNotifications();
    });
    
    // Welcome notification
    addNotification('Welcome to Cortex! Upload PDF documents to get started.', 'info');
    
    // Initially populate with any existing notifications
    updateNotificationPanel();
    
    // Show the panel initially if there are notifications
    if (notifications.length > 0) {
        setTimeout(() => {
            panel.classList.add('active');
            toggleIcon.classList.remove('fa-chevron-down');
            toggleIcon.classList.add('fa-chevron-up');
        }, 1000);
    }
}

// Add a notification to the panel
function addNotification(message, type = 'info') {
    // Create notification object with timestamp
    const notification = {
        id: Date.now(),
        message: message,
        type: type,
        timestamp: new Date(),
        read: false
    };
    
    // Add to beginning of array (newest first)
    notifications.unshift(notification);
    
    // Limit the number of notifications
    if (notifications.length > maxNotifications) {
        notifications = notifications.slice(0, maxNotifications);
    }
    
    // Update the panel
    updateNotificationPanel();
    
    // Update notification counter
    updateNotificationCounter();
    
    return notification.id;
}

// Update a notification by ID
function updateNotification(id, message, type) {
    const index = notifications.findIndex(n => n.id === id);
    if (index !== -1) {
        notifications[index].message = message;
        notifications[index].type = type;
        notifications[index].timestamp = new Date();
        updateNotificationPanel();
    }
}

// Remove a notification by ID
function removeNotification(id) {
    notifications = notifications.filter(n => n.id !== id);
    updateNotificationPanel();
    updateNotificationCounter();
}

// Clear all notifications
function clearNotifications() {
    notifications = [];
    updateNotificationPanel();
    resetNotificationCounter();
}

// Update notification counter
function updateNotificationCounter() {
    const badge = document.getElementById('notification-count');
    const unreadCount = notifications.filter(n => !n.read).length;
    
    badge.textContent = unreadCount;
    
    if (unreadCount > 0) {
        badge.classList.remove('hidden');
    } else {
        badge.classList.add('hidden');
    }
}

// Reset notification counter
function resetNotificationCounter() {
    // Mark all as read
    notifications.forEach(n => n.read = true);
    updateNotificationCounter();
}

// Update the notification panel UI
function updateNotificationPanel() {
    const list = document.getElementById('notification-list');
    
    // Clear current notifications
    list.innerHTML = '';
    
    if (notifications.length === 0) {
        // Show empty state
        const emptyEl = document.createElement('div');
        emptyEl.className = 'empty-notifications';
        emptyEl.textContent = 'No notifications';
        list.appendChild(emptyEl);
        return;
    }
    
    // Add each notification to the panel
    notifications.forEach(notification => {
        const notifItem = document.createElement('div');
        notifItem.className = `notification-item notification-${notification.type}`;
        
        let icon;
        switch(notification.type) {
            case 'success':
                icon = '<i class="fas fa-check-circle"></i>';
                break;
            case 'warning':
                icon = '<i class="fas fa-exclamation-triangle"></i>';
                break;
            case 'error':
                icon = '<i class="fas fa-times-circle"></i>';
                break;
            default: // info
                icon = '<i class="fas fa-info-circle"></i>';
        }
        
        // Format time
        const timeStr = formatNotificationTime(notification.timestamp);
        
        notifItem.innerHTML = `
            <div class="notification-icon">${icon}</div>
            <div class="notification-content">
                <div>${notification.message}</div>
                <div class="notification-time">${timeStr}</div>
            </div>
            <div class="notification-dismiss" data-id="${notification.id}">
                <i class="fas fa-times"></i>
            </div>
        `;
        
        list.appendChild(notifItem);
    });
    
    // Add event listeners for dismiss buttons
    document.querySelectorAll('.notification-dismiss').forEach(btn => {
        btn.addEventListener('click', e => {
            e.stopPropagation();
            const id = parseInt(btn.dataset.id);
            removeNotification(id);
        });
    });
}

// Helper to format notification time
function formatNotificationTime(date) {
    const now = new Date();
    const diff = Math.floor((now - date) / 1000); // diff in seconds
    
    if (diff < 60) {
        return 'Just now';
    } else if (diff < 3600) {
        const mins = Math.floor(diff / 60);
        return `${mins} minute${mins > 1 ? 's' : ''} ago`;
    } else if (diff < 86400) {
        const hours = Math.floor(diff / 3600);
        return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    } else {
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
}

// Replace the showToast function to use our notification system
function showNotification(message, type = 'info') {
    return addNotification(message, type);
}
