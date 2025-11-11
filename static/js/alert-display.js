/**
 * Alert Display - UI Only
 * Handles showing/hiding alert banners
 * Django backend determines WHAT alerts to show, this only handles the UI display
 */

// Dismiss notification banner
function dismissNotification(type) {
	if (type === 'kyc') {
		const kycNotification = document.getElementById('kycNotification');
		if (kycNotification) {
			kycNotification.style.display = 'none';
			// Save dismissal to localStorage to prevent showing again this session
			localStorage.setItem('kyc_notification_dismissed', 'true');
		}
	} else if (type === 'admin') {
		const adminNotification = document.getElementById('adminNotification');
		if (adminNotification) {
			adminNotification.style.display = 'none';
			// Save dismissal to localStorage
			localStorage.setItem('admin_notification_dismissed', 'true');
		}
	}
}

// Show transfer success alert (called after successful transfer - UI only)
function showTransferSuccess() {
	const alert = document.getElementById('transferSuccessAlert');
	if (alert) {
		alert.style.display = 'flex';

		// Fade out after 3 seconds
		setTimeout(() => {
			alert.style.animation = 'fadeOut 0.5s ease-out';
			setTimeout(() => {
				alert.style.display = 'none';
				alert.style.animation = '';
			}, 500);
		}, 3000);
	}
}

// Check if notifications should be shown on page load
document.addEventListener('DOMContentLoaded', function() {
	// Check if KYC notification should be shown
	// NOTE: Django should add a data attribute to control this
	const kycNotification = document.getElementById('kycNotification');
	if (kycNotification && kycNotification.hasAttribute('data-show')) {
		// Only show if not dismissed this session
		if (localStorage.getItem('kyc_notification_dismissed') !== 'true') {
			kycNotification.style.display = 'block';
		}
	}

	// Check if admin notification should be shown
	// NOTE: Django should add a data attribute to control this
	const adminNotification = document.getElementById('adminNotification');
	if (adminNotification && adminNotification.hasAttribute('data-show')) {
		// Only show if not dismissed this session
		if (localStorage.getItem('admin_notification_dismissed') !== 'true') {
			adminNotification.style.display = 'block';
		}
	}

	// Clear dismissal flags when user logs out (if logout link exists)
	const logoutLink = document.querySelector('a[href*="logout"]');
	if (logoutLink) {
		logoutLink.addEventListener('click', function() {
			localStorage.removeItem('kyc_notification_dismissed');
			localStorage.removeItem('admin_notification_dismissed');
		});
	}
});
