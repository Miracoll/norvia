/**
 * Theme Toggle - Light/Dark Mode
 * Handles theme switching and persistence
 */

function toggleTheme() {
	const body = document.body;
	const mainWrapper = document.getElementById('main-wrapper');
	const lightIcon = document.getElementById('theme-icon-light');
	const darkIcon = document.getElementById('theme-icon-dark');

	// Toggle between light and dark
	if (body.getAttribute('data-theme-version') === 'dark') {
		// Switch to light
		body.setAttribute('data-theme-version', 'light');
		mainWrapper.setAttribute('data-theme-version', 'light');
		lightIcon.style.display = 'block';
		darkIcon.style.display = 'none';
		localStorage.setItem('theme', 'light');
	} else {
		// Switch to dark
		body.setAttribute('data-theme-version', 'dark');
		mainWrapper.setAttribute('data-theme-version', 'dark');
		lightIcon.style.display = 'none';
		darkIcon.style.display = 'block';
		localStorage.setItem('theme', 'dark');
	}
}

// Load saved theme on page load
document.addEventListener('DOMContentLoaded', function() {
	const savedTheme = localStorage.getItem('theme') || 'light';
	const body = document.body;
	const mainWrapper = document.getElementById('main-wrapper');
	const lightIcon = document.getElementById('theme-icon-light');
	const darkIcon = document.getElementById('theme-icon-dark');

	body.setAttribute('data-theme-version', savedTheme);
	mainWrapper.setAttribute('data-theme-version', savedTheme);

	if (savedTheme === 'dark') {
		lightIcon.style.display = 'none';
		darkIcon.style.display = 'block';
	} else {
		lightIcon.style.display = 'block';
		darkIcon.style.display = 'none';
	}
});
