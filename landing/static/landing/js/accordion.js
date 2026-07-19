/**
 * Accordion Interactivity Handler
 * Manages the opening and closing of accordion items
 */

document.addEventListener('DOMContentLoaded', function() {
    const accordionItems = document.querySelectorAll('.accordion-item');
    
    accordionItems.forEach(item => {
        const header = item.querySelector('.accordion-header');
        const button = item.querySelector('.toggle-arrow-icon');
        
        if (header) {
            header.addEventListener('click', function() {
                toggleAccordion(item);
            });
        }

        // Allow keyboard interaction (Enter or Space)
        if (button) {
            button.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    toggleAccordion(item);
                }
            });
        }
    });

    function toggleAccordion(item) {
        const isActive = item.classList.contains('active');
        
        // Close all other accordion items
        accordionItems.forEach(otherItem => {
            if (otherItem !== item && otherItem.classList.contains('active')) {
                otherItem.classList.remove('active');
                const button = otherItem.querySelector('.toggle-arrow-icon');
                if (button) {
                    button.setAttribute('aria-expanded', 'false');
                }
            }
        });
        
        // Toggle current item
        if (isActive) {
            item.classList.remove('active');
            const button = item.querySelector('.toggle-arrow-icon');
            if (button) {
                button.setAttribute('aria-expanded', 'false');
            }
        } else {
            item.classList.add('active');
            const button = item.querySelector('.toggle-arrow-icon');
            if (button) {
                button.setAttribute('aria-expanded', 'true');
            }
        }
    }

    // Optional: Smooth scroll to the expanded item
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.attributeName === 'class') {
                const target = mutation.target;
                if (target.classList.contains('active')) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            }
        });
    });

    accordionItems.forEach(item => {
        observer.observe(item, { attributes: true, attributeFilter: ['class'] });
    });
});
