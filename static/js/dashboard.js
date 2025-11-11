/**
 * Dashboard JavaScript
 * Handles wallet UI, market data, and chart rendering
 * NOTE: All data comes from Django - this only handles UI display and API calls for live market data
 */

// ============================================================================
// Wallet UI State Management (UI only - Django provides the data)
// ============================================================================

let tradingBalanceType = 'deposit';
let holdingBalanceType = 'deposit';
let tradingBalanceVisible = true;
let holdingBalanceVisible = true;

// Trading Wallet UI Functions
function showTradingBalance(type) {
	tradingBalanceType = type;
	document.getElementById('tradingDepositBtn').classList.toggle('active', type === 'deposit');
	document.getElementById('tradingTradingBtn').classList.toggle('active', type === 'trading');
	updateTradingDisplay();
}

function toggleTradingBalance() {
	tradingBalanceVisible = !tradingBalanceVisible;
	document.getElementById('tradingEyeIcon').textContent = tradingBalanceVisible ? 'visibility_off' : 'visibility';
	updateTradingDisplay();
}

function updateTradingDisplay() {
	const balanceEl = document.getElementById('tradingBalanceDisplay');
	const btcEl = document.getElementById('tradingBtcValue');

	// Get values from Django-rendered elements' data attributes
	const depositUsd = balanceEl.getAttribute('data-deposit-usd');
	const tradingUsd = balanceEl.getAttribute('data-trading-usd');
	const depositBtc = btcEl.getAttribute('data-deposit-btc');
	const tradingBtc = btcEl.getAttribute('data-trading-btc');

	if (tradingBalanceVisible) {
		if (tradingBalanceType === 'deposit') {
			balanceEl.textContent = depositUsd;
			btcEl.textContent = depositBtc;
		} else {
			balanceEl.textContent = tradingUsd;
			btcEl.textContent = tradingBtc;
		}
	} else {
		balanceEl.textContent = '••••••';
		btcEl.textContent = '••••••';
	}
}

// Holding Wallet UI Functions
function showHoldingBalance(type) {
	holdingBalanceType = type;
	document.getElementById('holdingDepositBtn').classList.toggle('active', type === 'deposit');
	document.getElementById('holdingTradingBtn').classList.toggle('active', type === 'trading');
	updateHoldingDisplay();
}

function toggleHoldingBalance() {
	holdingBalanceVisible = !holdingBalanceVisible;
	document.getElementById('holdingEyeIcon').textContent = holdingBalanceVisible ? 'visibility_off' : 'visibility';
	updateHoldingDisplay();
}

function updateHoldingDisplay() {
	const balanceEl = document.getElementById('holdingBalanceDisplay');
	const btcEl = document.getElementById('holdingBtcValue');

	// Get values from Django-rendered elements' data attributes
	const depositUsd = balanceEl.getAttribute('data-deposit-usd');
	const tradingUsd = balanceEl.getAttribute('data-trading-usd');
	const depositBtc = btcEl.getAttribute('data-deposit-btc');
	const tradingBtc = btcEl.getAttribute('data-trading-btc');

	if (holdingBalanceVisible) {
		if (holdingBalanceType === 'deposit') {
			balanceEl.textContent = depositUsd;
			btcEl.textContent = depositBtc;
		} else {
			balanceEl.textContent = tradingUsd;
			btcEl.textContent = tradingBtc;
		}
	} else {
		balanceEl.textContent = '••••••';
		btcEl.textContent = '••••••';
	}
}

// ============================================================================
// Real-Time Market Data Functions (CoinGecko API)
// ============================================================================

let currentCrypto = 'bitcoin';
let currentDays = 30;
let marketChart = null;

async function fetchMarketData(cryptoId) {
	try {
		// Show loading state
		document.getElementById('market-cap').textContent = 'Loading...';
		document.getElementById('btc-price').textContent = 'Loading...';
		document.getElementById('btc-change').textContent = 'Loading...';
		document.getElementById('btc-volume').textContent = 'Loading...';

		const response = await fetch(`https://api.coingecko.com/api/v3/coins/${cryptoId}?localization=false&tickers=false&community_data=false&developer_data=false`, {
			method: 'GET',
			mode: 'cors',
			headers: {
				'Accept': 'application/json'
			}
		});

		if (!response.ok) {
			throw new Error(`HTTP error! status: ${response.status}`);
		}

		const data = await response.json();

		// Validate that we have the required data
		if (!data.market_data || !data.market_data.market_cap || !data.market_data.current_price) {
			throw new Error('Invalid data structure received from API');
		}

		// Update Market Cap
		const marketCap = data.market_data.market_cap.usd;
		document.getElementById('market-cap').textContent = '$' + (marketCap / 1e9).toFixed(2) + 'B';

		// Update Price
		const price = data.market_data.current_price.usd;
		document.getElementById('btc-price').textContent = '$' + price.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});

		// Update 24h Change
		const change24h = data.market_data.price_change_percentage_24h;
		const changeEl = document.getElementById('btc-change');
		const changeSign = change24h >= 0 ? '+' : '';
		changeEl.innerHTML = `${changeSign}${change24h.toFixed(2)}%`;
		changeEl.style.color = change24h >= 0 ? '#16a34a' : '#ef4444';

		// Update 24h Volume
		const volume = data.market_data.total_volume.usd;
		document.getElementById('btc-volume').textContent = '$' + (volume / 1e9).toFixed(2) + 'B';

		// Update labels based on selected crypto
		const symbol = data.symbol.toUpperCase();
		document.getElementById('btc-price').previousElementSibling.textContent = `${symbol} Price`;

		// Fetch and update chart
		await updateMarketChart(cryptoId, data.name, currentDays);
	} catch (error) {
		console.error('Error fetching market data:', error);
		console.error('Error details:', {
			message: error.message,
			cryptoId: cryptoId,
			timestamp: new Date().toISOString()
		});

		// Show specific error messages
		const errorMsg = error.message.includes('HTTP error') ? 'API Error' :
		                 error.message.includes('Failed to fetch') ? 'Connection Error' :
		                 'Error loading';

		document.getElementById('market-cap').textContent = errorMsg;
		document.getElementById('btc-price').textContent = errorMsg;
		document.getElementById('btc-change').textContent = errorMsg;
		document.getElementById('btc-volume').textContent = errorMsg;
	}
}

async function updateMarketChart(cryptoId, cryptoName, days = 30) {
	try {
		// Fetch price data for selected period
		const response = await fetch(`https://api.coingecko.com/api/v3/coins/${cryptoId}/market_chart?vs_currency=usd&days=${days}`, {
			method: 'GET',
			mode: 'cors',
			headers: {
				'Accept': 'application/json'
			}
		});

		if (!response.ok) {
			throw new Error(`HTTP error! status: ${response.status}`);
		}

		const data = await response.json();

		// Validate data
		if (!data.prices || !Array.isArray(data.prices)) {
			throw new Error('Invalid chart data received');
		}

		// Format data for ApexCharts [timestamp, price]
		const chartData = data.prices.map(item => [item[0], item[1].toFixed(2)]);

		if (marketChart) {
			// Update existing chart with new data and options
			marketChart.updateOptions({
				xaxis: {
					type: 'datetime',
					labels: {
						style: {
							colors: '#6c757d',
							fontSize: '12px'
						},
						datetimeUTC: false,
						format: days <= 7 ? 'dd MMM' : days <= 30 ? 'dd MMM' : days <= 90 ? 'MMM yyyy' : 'MMM yyyy'
					}
				}
			});
			marketChart.updateSeries([{
				name: cryptoName,
				data: chartData
			}]);
		} else {
			// Create new chart
			const options = {
				series: [{
					name: cryptoName,
					data: chartData
				}],
				chart: {
					type: 'area',
					height: 350,
					toolbar: {
						show: false
					},
					zoom: {
						enabled: false
					}
				},
				colors: ['#01A3FF'],
				dataLabels: {
					enabled: false
				},
				stroke: {
					width: 2,
					curve: 'smooth'
				},
				fill: {
					type: 'gradient',
					gradient: {
						shadeIntensity: 1,
						opacityFrom: 0.4,
						opacityTo: 0.1,
						stops: [0, 100]
					}
				},
				xaxis: {
					type: 'datetime',
					labels: {
						style: {
							colors: '#6c757d',
							fontSize: '12px'
						},
						datetimeUTC: false,
						format: days <= 7 ? 'dd MMM' : days <= 30 ? 'dd MMM' : days <= 90 ? 'MMM yyyy' : 'MMM yyyy'
					}
				},
				yaxis: {
					labels: {
						style: {
							colors: '#6c757d',
							fontSize: '12px'
						},
						formatter: function(value) {
							return '$' + value.toLocaleString();
						}
					}
				},
				tooltip: {
					x: {
						format: 'dd MMM yyyy'
					},
					y: {
						formatter: function(value) {
							return '$' + value.toLocaleString();
						}
					}
				},
				grid: {
					borderColor: '#e5e7eb'
				}
			};

			marketChart = new ApexCharts(document.querySelector("#activity1"), options);
			marketChart.render();
		}
	} catch (error) {
		console.error('Error updating chart:', error);
	}
}

// Update market data every 60 seconds
function startMarketDataUpdates() {
	fetchMarketData(currentCrypto);
	setInterval(() => fetchMarketData(currentCrypto), 60000); // Update every 60 seconds
}

// Helper function to get crypto display name
function getCryptoName(cryptoId) {
	const names = {
		'bitcoin': 'Bitcoin',
		'ethereum': 'Ethereum',
		'binancecoin': 'Binance Coin',
		'solana': 'Solana',
		'ripple': 'Ripple'
	};
	return names[cryptoId] || cryptoId;
}

// ============================================================================
// Initialize Everything
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
	// Crypto selector event
	const cryptoSelector = document.getElementById('crypto-selector');
	if (cryptoSelector) {
		cryptoSelector.addEventListener('change', function() {
			currentCrypto = this.value;
			fetchMarketData(currentCrypto);
		});
	}

	// Date range buttons event
	const dateRangeButtons = document.querySelectorAll('.date-range-btn');
	dateRangeButtons.forEach(button => {
		button.addEventListener('click', function() {
			// Remove active class from all buttons
			dateRangeButtons.forEach(btn => btn.classList.remove('active'));

			// Add active class to clicked button
			this.classList.add('active');

			// Update current days and refresh chart
			currentDays = parseInt(this.getAttribute('data-days'));
			updateMarketChart(currentCrypto, getCryptoName(currentCrypto), currentDays);
		});
	});

	// Start fetching market data
	startMarketDataUpdates();

	// Initialize Swiper for wallet cards
	const walletSwiper = new Swiper('.wallet-swiper', {
		slidesPerView: 1,
		spaceBetween: 0,
		speed: 400,
		effect: 'slide',
		grabCursor: true,
		touchRatio: 1,
		touchAngle: 45,
		threshold: 5,
		resistanceRatio: 0.85,
		pagination: {
			el: '.swiper-pagination',
			clickable: true,
			dynamicBullets: false,
		},
		on: {
			init: function () {
				console.log('Wallet swiper initialized');
			},
			slideChange: function () {
				console.log('Wallet changed to:', this.activeIndex === 0 ? 'Trading' : 'Holding');
				// Hide swipe hint after first swipe
				const swiperEl = document.querySelector('.wallet-swiper');
				if (swiperEl) {
					swiperEl.classList.add('swiped');
				}
			},
			touchStart: function() {
				console.log('Touch started on wallet swiper');
			},
			touchMove: function() {
				// Hide hint when user starts swiping
				const swiperEl = document.querySelector('.wallet-swiper');
				if (swiperEl) {
					swiperEl.classList.add('swiped');
				}
			}
		},
	});
});
