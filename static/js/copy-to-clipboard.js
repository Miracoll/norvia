/**
 * Copy to Clipboard Functionality
 * Handles all copy buttons across the application
 */

document.addEventListener('DOMContentLoaded', function() {
	// Find all copy buttons (multiple class names used across the site)
	const copyButtons = document.querySelectorAll('.btn-copy, .copy-button, [data-copy]');

	copyButtons.forEach(button => {
		button.addEventListener('click', function(e) {
			e.preventDefault();

			// Find the text to copy
			let textToCopy = '';

			// Method 1: Check for data-copy attribute (contains text directly)
			if (this.hasAttribute('data-copy')) {
				textToCopy = this.getAttribute('data-copy');
			}
			// Method 2: Check for data-copy-target attribute (contains ID of element to copy)
			else if (this.hasAttribute('data-copy-target')) {
				const targetId = this.getAttribute('data-copy-target');
				const targetElement = document.getElementById(targetId);
				if (targetElement) {
					textToCopy = targetElement.value || targetElement.textContent;
				}
			}
			// Method 3: Look for sibling input field
			else {
				const parent = this.closest('.referral-link-input-group, .wallet-address-display');
				if (parent) {
					const input = parent.querySelector('input, .address-display, .referral-link-input');
					if (input) {
						textToCopy = input.value || input.textContent.trim();
					}
				}
			}

			// Copy to clipboard
			if (textToCopy) {
				navigator.clipboard.writeText(textToCopy).then(() => {
					// Store original HTML and style
					const originalHTML = this.innerHTML;
					const originalBackground = this.style.background;

					// Update button with success feedback
					this.innerHTML = '<i class="material-icons">check</i>Copied!';
					this.style.background = '#10b981';

					// Reset after 2 seconds
					setTimeout(() => {
						this.innerHTML = originalHTML;
						this.style.background = originalBackground;
					}, 2000);
				}).catch(err => {
					console.error('Failed to copy text: ', err);
					alert('Failed to copy to clipboard. Please try again.');
				});
			}
		});
	});

	// Also handle any icons with content_copy that are standalone (not inside a button)
	const copyIcons = document.querySelectorAll('.material-icons');
	copyIcons.forEach(icon => {
		if (icon.textContent.trim() === 'content_copy' && !icon.closest('button')) {
			icon.style.cursor = 'pointer';
			icon.addEventListener('click', function(e) {
				e.preventDefault();

				// Find closest parent with data to copy
				const parent = this.closest('.wallet-address-display, .referral-link-input-group, '.address-display-container');
				if (parent) {
					const input = parent.querySelector('input, .address-display, .referral-link-input');
					if (input) {
						const textToCopy = input.value || input.textContent.trim();

						navigator.clipboard.writeText(textToCopy).then(() => {
							// Visual feedback
							const originalIcon = this.textContent;
							this.textContent = 'check';
							this.style.color = '#10b981';

							setTimeout(() => {
								this.textContent = originalIcon;
								this.style.color = '';
							}, 2000);
						}).catch(err => {
							console.error('Failed to copy: ', err);
							alert('Failed to copy to clipboard. Please try again.');
						});
					}
				}
			});
		}
	});
});
