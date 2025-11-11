/**
 * Admin Mobile Sidebar Toggle
 * Handles mobile menu functionality for Norvia.io Admin Panel
 */

(function() {
	'use strict';

	// Wait for DOM to be ready
	document.addEventListener('DOMContentLoaded', function() {

		// Create overlay element if it doesn't exist
		let overlay = document.querySelector('.sidebar-overlay');
		if (!overlay) {
			overlay = document.createElement('div');
			overlay.className = 'sidebar-overlay';
			document.body.appendChild(overlay);
		}

		// Get elements
		const hamburger = document.querySelector('.hamburger');
		const sidebar = document.querySelector('.dlabnav');

		if (!hamburger || !sidebar) {
			console.warn('Hamburger or sidebar not found');
			return;
		}

		// Toggle sidebar function
		function toggleSidebar() {
			const isActive = sidebar.classList.contains('active');

			if (isActive) {
				// Close sidebar
				hamburger.classList.remove('is-active');
				sidebar.classList.remove('active');
				overlay.classList.remove('active');
				document.body.style.overflow = '';
			} else {
				// Open sidebar
				hamburger.classList.add('is-active');
				sidebar.classList.add('active');
				overlay.classList.add('active');
				document.body.style.overflow = 'hidden';
			}
		}

		// Close sidebar function
		function closeSidebar() {
			hamburger.classList.remove('is-active');
			sidebar.classList.remove('active');
			overlay.classList.remove('active');
			document.body.style.overflow = '';
		}

		// Hamburger click event
		hamburger.addEventListener('click', function(e) {
			e.stopPropagation();
			toggleSidebar();
		});

		// Overlay click event - close sidebar
		overlay.addEventListener('click', function() {
			closeSidebar();
		});

		// Close sidebar when clicking on menu items on mobile
		const menuLinks = sidebar.querySelectorAll('.dlabnav a');
		menuLinks.forEach(function(link) {
			link.addEventListener('click', function(e) {
				// Only close on mobile and if it's not a dropdown toggle
				if (window.innerWidth < 768 && !link.classList.contains('has-arrow')) {
					// Add small delay to allow page navigation
					setTimeout(closeSidebar, 300);
				}
			});
		});

		// Close sidebar on window resize to desktop
		let resizeTimer;
		window.addEventListener('resize', function() {
			clearTimeout(resizeTimer);
			resizeTimer = setTimeout(function() {
				if (window.innerWidth >= 768) {
					closeSidebar();
				}
			}, 250);
		});

		// Close sidebar on escape key
		document.addEventListener('keydown', function(e) {
			if (e.key === 'Escape' && sidebar.classList.contains('active')) {
				closeSidebar();
			}
		});

	});

})();
