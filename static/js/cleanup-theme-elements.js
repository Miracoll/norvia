/**
 * Theme Cleanup - Remove Floating Buttons and Popups
 * Removes promotional elements added by the theme template
 */

// Track elements we've already processed to avoid re-processing
const processedElements = new WeakSet();

// Function to remove floating buttons and sale popups
function removeFloatingButtons() {
	// Remove sale popups and banners
	const saleElements = document.querySelectorAll('.dlab-sale-banner, .dzSaleBanner, #dzSaleBanner, .dlab-demo-panel, [class*="sale-banner"]');
	saleElements.forEach(el => {
		if (!processedElements.has(el)) {
			processedElements.add(el);
			el.remove();
		}
	});

	// Remove chatbox toggle button if it exists
	const chatboxToggle = document.querySelector('.chatbox-icon-toggle, .dlab-chatbox-toggle, [data-target=".chatbox"]');
	if (chatboxToggle && !processedElements.has(chatboxToggle)) {
		processedElements.add(chatboxToggle);
		chatboxToggle.remove();
	}

	// Remove any other floating buttons
	const floatingButtons = document.querySelectorAll('.add-menu-sidebar, .sidebar-right-trigger, .fixed-content-box, .DZ-bt-buy-now, .DZ-bt-support-now');
	floatingButtons.forEach(btn => {
		if (!processedElements.has(btn)) {
			processedElements.add(btn);
			btn.remove();
		}
	});

	// Remove any direct body children that are sale popups (more targeted approach)
	document.querySelectorAll('body > div').forEach(el => {
		// Skip if already processed
		if (processedElements.has(el)) {
			return;
		}

		// Skip swiper-related elements
		if (el.classList.contains('swiper-notification') ||
			el.classList.contains('swiper-pagination') ||
			el.closest('.swiper')) {
			return;
		}

		// Skip main wrapper and essential elements
		if (el.id === 'main-wrapper' ||
			el.classList.contains('header') ||
			el.classList.contains('dlabnav') ||
			el.classList.contains('content-body') ||
			el.classList.contains('footer')) {
			return;
		}

		const style = window.getComputedStyle(el);

		// Check if it's a sale/promotional popup by text content
		if (el.textContent && (
			el.textContent.includes('DIWALI') ||
			el.textContent.includes('Diwali') ||
			el.textContent.includes('DHAMAKA') ||
			el.textContent.includes('GRAB SALE')
		)) {
			processedElements.add(el);
			el.remove();
			return;
		}

		// Remove fixed position elements with very high z-index (popups/overlays)
		// but skip Swiper notification elements
		if (style.position === 'fixed' && !el.classList.contains('swiper-notification')) {
			const zIndex = parseInt(style.zIndex);
			// Only remove if z-index is extremely high (typical for promotional popups)
			if (zIndex > 9000) {
				processedElements.add(el);
				el.remove();
			}
		}
	});
}

// Run immediately
removeFloatingButtons();

// Run after DOM is fully loaded
document.addEventListener('DOMContentLoaded', function() {
	removeFloatingButtons();
});

// Run after short delays to catch dynamically added elements
setTimeout(removeFloatingButtons, 100);
setTimeout(removeFloatingButtons, 500);
setTimeout(removeFloatingButtons, 1000);
setTimeout(removeFloatingButtons, 2000);

// Watch for new elements being added with throttling
let observerTimeout;
const observer = new MutationObserver(function(mutations) {
	// Throttle the observer to avoid excessive calls
	clearTimeout(observerTimeout);
	observerTimeout = setTimeout(() => {
		mutations.forEach(function(mutation) {
			if (mutation.addedNodes.length) {
				mutation.addedNodes.forEach(node => {
					// Only process element nodes
					if (node.nodeType === 1) {
						// Check if it's a sale/promo element
						if (node.classList && (
							node.classList.contains('dlab-sale-banner') ||
							node.classList.contains('dzSaleBanner') ||
							node.classList.contains('dlab-demo-panel') ||
							node.id === 'dzSaleBanner'
						)) {
							node.remove();
						}
						// Check text content for promotional popup
						else if (node.textContent && (
							node.textContent.includes('DIWALI') ||
							node.textContent.includes('DHAMAKA') ||
							node.textContent.includes('GRAB SALE')
						)) {
							const style = window.getComputedStyle(node);
							if (style.position === 'fixed') {
								node.remove();
							}
						}
					}
				});
			}
		});
	}, 100); // Throttle to 100ms
});

// Start observing
if (document.body) {
	observer.observe(document.body, {
		childList: true,
		subtree: false // Only watch direct children of body
	});
}
