// Valyrian Games Leaderboard - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Format dates
    document.querySelectorAll('.format-date').forEach(element => {
        const dateStr = element.textContent;
        if (dateStr && dateStr !== 'N/A') {
            try {
                const date = new Date(dateStr);
                element.textContent = date.toLocaleDateString();
            } catch (e) {
                console.error('Error formatting date:', e);
            }
        }
    });

    // Format timestamps
    document.querySelectorAll('.format-datetime').forEach(element => {
        const dateStr = element.textContent;
        if (dateStr && dateStr !== 'N/A') {
            try {
                const date = new Date(dateStr);
                element.textContent = date.toLocaleString();
            } catch (e) {
                console.error('Error formatting datetime:', e);
            }
        }
    });

    // Handle collapsible sections
    document.querySelectorAll('.collapse-toggle').forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                const isExpanded = this.getAttribute('aria-expanded') === 'true';
                
                if (isExpanded) {
                    targetElement.classList.remove('show');
                    this.setAttribute('aria-expanded', 'false');
                    this.textContent = this.getAttribute('data-expand-text') || 'Show More';
                } else {
                    targetElement.classList.add('show');
                    this.setAttribute('aria-expanded', 'true');
                    this.textContent = this.getAttribute('data-collapse-text') || 'Show Less';
                }
            }
        });
    });
});

// Utility function to format TrueSkill ratings
function formatRating(mu, sigma) {
    return `${mu.toFixed(1)} ± ${sigma.toFixed(2)}`;
}

// Utility function to format conservative skill
function formatConservativeSkill(mu, sigma) {
    return (mu - 3 * sigma).toFixed(1);
}

// Utility function to create a rating bar
function createRatingBar(container, mu, sigma, maxRating = 50) {
    const conservativeSkill = mu - 3 * sigma;
    const percentage = (conservativeSkill / maxRating) * 100;
    
    const bar = document.createElement('div');
    bar.className = 'rating-bar';
    
    const fill = document.createElement('div');
    fill.className = 'rating-bar-fill';
    fill.style.width = `${Math.max(0, Math.min(100, percentage))}%`;
    
    bar.appendChild(fill);
    container.appendChild(bar);
    
    const label = document.createElement('small');
    label.className = 'd-block text-muted mt-1';
    label.textContent = `Conservative: ${conservativeSkill.toFixed(1)}`;
    container.appendChild(label);
}
