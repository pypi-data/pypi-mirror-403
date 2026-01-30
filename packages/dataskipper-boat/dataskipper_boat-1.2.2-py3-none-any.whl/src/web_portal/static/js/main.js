/**
 * RTU Portal - Main JavaScript
 * Lightweight, vanilla JS implementation
 */

// Global state
let connectionStatus = 'unknown';

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    checkConnection();
    setInterval(checkConnection, 30000); // Check every 30 seconds
});

/**
 * Check API connection status
 */
async function checkConnection() {
    const indicator = document.getElementById('connection-status');
    const statusText = document.getElementById('status-text');

    try {
        const response = await fetch('/api/metrics', { timeout: 5000 });
        if (response.ok) {
            connectionStatus = 'ok';
            indicator.className = 'status-indicator status-ok';
            statusText.textContent = 'Connected';
        } else {
            throw new Error('API error');
        }
    } catch (error) {
        connectionStatus = 'error';
        indicator.className = 'status-indicator status-error';
        statusText.textContent = 'Disconnected';
    }
}

/**
 * Update last refresh timestamp
 */
function updateLastRefresh() {
    const el = document.getElementById('last-update');
    if (el) {
        const now = new Date();
        el.textContent = `Last update: ${now.toLocaleTimeString()}`;
    }
}

/**
 * Show notification toast
 */
function showNotification(message, type = 'info') {
    // Remove existing notifications
    document.querySelectorAll('.notification').forEach(n => n.remove());

    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;

    document.body.appendChild(notification);

    // Auto-remove after 4 seconds
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Format timestamp
 */
function formatTimestamp(isoString) {
    const date = new Date(isoString);
    return date.toLocaleString();
}

/**
 * Format bytes to human readable
 */
function formatBytes(bytes, decimals = 2) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i];
}

/**
 * Debounce function for performance
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * API helper with error handling
 */
async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            ...options,
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'API request failed');
        }

        return data;
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
        throw error;
    }
}

/**
 * Service Worker registration for push notifications
 */
async function registerServiceWorker() {
    if ('serviceWorker' in navigator && 'PushManager' in window) {
        try {
            const registration = await navigator.serviceWorker.register('/static/js/sw.js');
            console.log('ServiceWorker registered:', registration);
            return registration;
        } catch (error) {
            console.error('ServiceWorker registration failed:', error);
        }
    }
    return null;
}

/**
 * Request push notification permission
 */
async function requestNotificationPermission() {
    if (!('Notification' in window)) {
        showNotification('Push notifications not supported', 'error');
        return false;
    }

    const permission = await Notification.requestPermission();
    return permission === 'granted';
}

/**
 * Show local notification (when page is visible)
 */
function showLocalNotification(title, body, options = {}) {
    if (Notification.permission === 'granted') {
        new Notification(title, {
            body,
            icon: '/static/icon.png',
            badge: '/static/badge.png',
            tag: options.tag || 'rtu-alert',
            ...options
        });
    }
}

/**
 * Keyboard shortcuts handler
 */
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + K: Focus search (if exists)
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        const searchInput = document.querySelector('#log-search, #search-input');
        if (searchInput) {
            e.preventDefault();
            searchInput.focus();
        }
    }

    // Escape: Close modals
    if (e.key === 'Escape') {
        const modal = document.querySelector('.modal[style*="flex"]');
        if (modal) {
            modal.style.display = 'none';
        }
    }
});

/**
 * Auto-refresh handler
 */
class AutoRefresh {
    constructor(callback, interval = 10000) {
        this.callback = callback;
        this.interval = interval;
        this.timerId = null;
        this.isActive = false;
    }

    start() {
        if (this.isActive) return;
        this.isActive = true;
        this.timerId = setInterval(() => this.callback(), this.interval);
    }

    stop() {
        this.isActive = false;
        if (this.timerId) {
            clearInterval(this.timerId);
            this.timerId = null;
        }
    }

    toggle() {
        if (this.isActive) {
            this.stop();
        } else {
            this.start();
        }
        return this.isActive;
    }
}

/**
 * Update connection status indicator
 */
function updateConnectionStatus(isConnected) {
    const indicator = document.getElementById('connection-status');
    const statusText = document.getElementById('status-text');

    if (!indicator || !statusText) return;

    if (isConnected) {
        connectionStatus = 'ok';
        indicator.className = 'status-indicator status-ok';
        statusText.textContent = 'Connected';
    } else {
        connectionStatus = 'error';
        indicator.className = 'status-indicator status-error';
        statusText.textContent = 'Disconnected';
    }
}

// Export for use in templates
window.RTUPortal = {
    checkConnection,
    updateLastRefresh,
    showNotification,
    escapeHtml,
    formatTimestamp,
    formatBytes,
    debounce,
    apiCall,
    registerServiceWorker,
    requestNotificationPermission,
    showLocalNotification,
    updateConnectionStatus,
    AutoRefresh
};
