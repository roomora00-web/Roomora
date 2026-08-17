/**
 * Roomora Mobile Native Enhancements
 * Features:
 * 1. Pull-To-Refresh Gesture with elastic physics & spinner
 * 2. Native Web Share API (WhatsApp, Telegram, System Sheet)
 * 3. Geolocation Near-Me Search
 * 4. Offline Vault (Local persistence for saved properties & active booking passes)
 */

(function() {
    'use strict';

    // =========================================================================
    // 1. Pull-To-Refresh Controller
    // =========================================================================
    let touchStartY = 0;
    let touchMoveY = 0;
    let isPulling = false;
    let ptrSpinner = null;
    const PULL_THRESHOLD = 75; // px needed to trigger reload

    function initPullToRefresh() {
        // Only activate on touch devices / mobile viewports <= 768px
        if (window.innerWidth > 768) return;

        // Create Pull to Refresh DOM element if not present
        if (!document.getElementById('roomora-ptr-indicator')) {
            ptrSpinner = document.createElement('div');
            ptrSpinner.id = 'roomora-ptr-indicator';
            ptrSpinner.innerHTML = `
                <div class="ptr-content">
                    <svg class="ptr-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                        <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/>
                    </svg>
                    <span class="ptr-text">Pull to refresh</span>
                </div>
            `;
            ptrSpinner.style.cssText = `
                position: fixed;
                top: -60px;
                left: 0;
                right: 0;
                height: 50px;
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 99999;
                pointer-events: none;
                transition: transform 0.15s ease-out, opacity 0.2s ease;
                opacity: 0;
            `;

            const style = document.createElement('style');
            style.textContent = `
                #roomora-ptr-indicator .ptr-content {
                    background: rgba(18, 20, 29, 0.95);
                    backdrop-filter: blur(16px);
                    -webkit-backdrop-filter: blur(16px);
                    border: 1px solid rgba(59, 130, 246, 0.3);
                    border-radius: 30px;
                    padding: 8px 16px;
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                    box-shadow: 0 8px 24px rgba(0,0,0,0.5);
                }
                #roomora-ptr-indicator .ptr-icon {
                    width: 18px;
                    height: 18px;
                    color: #60A5FA;
                    transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
                }
                #roomora-ptr-indicator .ptr-text {
                    font-size: 12px;
                    font-weight: 600;
                    color: #F8FAFC;
                    letter-spacing: -0.01em;
                }
                #roomora-ptr-indicator.refreshing .ptr-icon {
                    animation: ptrSpin 0.7s linear infinite;
                }
                @keyframes ptrSpin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
            `;
            document.head.appendChild(style);
            document.body.prepend(ptrSpinner);
        } else {
            ptrSpinner = document.getElementById('roomora-ptr-indicator');
        }

        window.addEventListener('touchstart', (e) => {
            if (window.scrollY === 0) {
                touchStartY = e.touches[0].clientY;
                isPulling = true;
            } else {
                isPulling = false;
            }
        }, { passive: true });

        window.addEventListener('touchmove', (e) => {
            if (!isPulling || window.scrollY > 0) return;

            touchMoveY = e.touches[0].clientY;
            const pullDistance = touchMoveY - touchStartY;

            if (pullDistance > 0 && pullDistance < 180) {
                const damped = Math.pow(pullDistance, 0.85); // Elastic resistance
                ptrSpinner.style.transform = `translateY(${damped}px)`;
                ptrSpinner.style.opacity = Math.min(damped / PULL_THRESHOLD, 1).toString();

                const icon = ptrSpinner.querySelector('.ptr-icon');
                const text = ptrSpinner.querySelector('.ptr-text');
                if (pullDistance >= PULL_THRESHOLD) {
                    if (icon) icon.style.transform = 'rotate(180deg)';
                    if (text) text.textContent = 'Release to refresh';
                } else {
                    if (icon) icon.style.transform = `rotate(${pullDistance * 2}deg)`;
                    if (text) text.textContent = 'Pull to refresh';
                }
            }
        }, { passive: true });

        window.addEventListener('touchend', () => {
            if (!isPulling) return;
            isPulling = false;

            const pullDistance = touchMoveY - touchStartY;
            touchStartY = 0;
            touchMoveY = 0;

            if (pullDistance >= PULL_THRESHOLD) {
                ptrSpinner.classList.add('refreshing');
                const text = ptrSpinner.querySelector('.ptr-text');
                if (text) text.textContent = 'Refreshing Roomora...';
                
                // Trigger reload
                setTimeout(() => {
                    window.location.reload();
                }, 350);
            } else {
                ptrSpinner.style.transform = 'translateY(0px)';
                ptrSpinner.style.opacity = '0';
            }
        });
    }

    // =========================================================================
    // 2. Native Web Share API
    // =========================================================================
    window.roomoraShare = async function(data) {
        const shareData = {
            title: data.title || document.title || 'Roomora Property',
            text: data.text || 'Check out this accommodation on Roomora!',
            url: data.url || window.location.href
        };

        if (navigator.share) {
            try {
                await navigator.share(shareData);
                console.log('[Roomora] Share successful');
            } catch (err) {
                if (err.name !== 'AbortError') {
                    fallbackCopyUrl(shareData.url);
                }
            }
        } else {
            fallbackCopyUrl(shareData.url);
        }
    };

    function fallbackCopyUrl(url) {
        navigator.clipboard.writeText(url).then(() => {
            if (typeof showNotification === 'function') {
                showNotification('Link Copied', 'Property link copied to clipboard!', 'SYSTEM');
            } else {
                alert('Property link copied to clipboard!');
            }
        }).catch(() => {
            prompt('Copy this property link:', url);
        });
    }

    // =========================================================================
    // 3. Geolocation "Near Me" Finder
    // =========================================================================
    window.roomoraNearMe = function() {
        if (!navigator.geolocation) {
            alert('Geolocation is not supported by your browser.');
            return;
        }

        if (typeof showNotification === 'function') {
            showNotification('Location', 'Finding accommodations near your location...', 'SYSTEM');
        }

        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const lat = pos.coords.latitude;
                const lng = pos.coords.longitude;
                // Redirect to property search with coordinates
                window.location.href = `/properties/?lat=${lat.toFixed(4)}&lng=${lng.toFixed(4)}&near_me=true`;
            },
            (err) => {
                console.warn('[Roomora] Geolocation failed:', err);
                if (typeof showNotification === 'function') {
                    showNotification('Location Error', 'Unable to retrieve location. Please allow location permissions.', 'CONFLICT');
                } else {
                    alert('Please allow location permissions to find properties near you.');
                }
            },
            { timeout: 10000, enableHighAccuracy: true }
        );
    };

    // =========================================================================
    // 4. Offline Vault (Local sync for saved items & booking pass)
    // =========================================================================
    const VAULT_KEY = 'roomora_offline_vault_v1';

    window.RoomoraVault = {
        getVault: function() {
            try {
                return JSON.parse(localStorage.getItem(VAULT_KEY)) || { savedProperties: [], bookingPasses: [] };
            } catch (e) {
                return { savedProperties: [], bookingPasses: [] };
            }
        },

        savePropertyToVault: function(property) {
            const vault = this.getVault();
            const exists = vault.savedProperties.some(p => p.id === property.id);
            if (!exists) {
                vault.savedProperties.unshift(property);
                // Keep max 20 offline properties
                vault.savedProperties = vault.savedProperties.slice(0, 20);
                localStorage.setItem(VAULT_KEY, JSON.stringify(vault));
            }
        },

        saveBookingPass: function(booking) {
            const vault = this.getVault();
            const exists = vault.bookingPasses.some(b => b.id === booking.id);
            if (!exists) {
                vault.bookingPasses.unshift(booking);
                localStorage.setItem(VAULT_KEY, JSON.stringify(vault));
            }
        }
    };

    // Auto-capture property details into vault when user visits a property page
    document.addEventListener('DOMContentLoaded', () => {
        initPullToRefresh();

        // Check if viewing a property detail page
        const propTitleEl = document.querySelector('.property-title, h1.prop-heading, #property-title');
        const propPriceEl = document.querySelector('.property-price, .prop-price-tag, #property-price');
        const propImgEl = document.querySelector('.property-main-img, .prop-gallery-img');

        if (propTitleEl && propPriceEl) {
            const propertyId = window.location.pathname.match(/\/properties\/(\d+)\/?/);
            if (propertyId && propertyId[1]) {
                window.RoomoraVault.savePropertyToVault({
                    id: propertyId[1],
                    title: propTitleEl.innerText.trim(),
                    price: propPriceEl.innerText.trim(),
                    image: propImgEl ? propImgEl.src : '/static/pwa/icons/icon-192.png',
                    url: window.location.pathname,
                    savedAt: new Date().toLocaleDateString()
                });
            }
        }
    });

})();
