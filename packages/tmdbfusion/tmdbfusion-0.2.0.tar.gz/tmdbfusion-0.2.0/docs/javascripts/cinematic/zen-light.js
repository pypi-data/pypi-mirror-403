// Cinematic Zen Light Controller

(function () {
    // Initial Position (Bottom Right)
    let state = {
        x: window.innerWidth - 80,
        y: window.innerHeight - 80,
        active: false,
        isDragging: false,
        startDragTime: 0
    };

    let container, overlay, orb;

    function updateCSS() {
        if (!container) return;
        container.style.setProperty('--zen-x', `${state.x}px`);
        container.style.setProperty('--zen-y', `${state.y}px`);
    }

    function toggleZen() {
        state.active = !state.active;
        if (state.active) {
            container.classList.add('zen-active');
        } else {
            container.classList.remove('zen-active');
        }
    }

    function init() {
        if (document.getElementById('zen-container')) return;

        container = document.createElement('div');
        container.id = 'zen-container';

        overlay = document.createElement('div');
        overlay.id = 'zen-overlay';

        orb = document.createElement('div');
        orb.id = 'zen-orb';

        container.appendChild(overlay);
        container.appendChild(orb);
        document.body.appendChild(container);

        updateCSS();

        // EVENTS

        // Drag Start
        const onDragStart = (e) => {
            if (e.target !== orb) return;
            state.isDragging = true;
            state.startDragTime = Date.now();
            e.preventDefault(); // Prevent text selection etc
        };

        // Drag Move
        const onDragMove = (e) => {
            if (!state.isDragging) return;

            // Support Mouse and Touch
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches ? e.touches[0].clientY : e.clientY;

            state.x = clientX;
            state.y = clientY;

            requestAnimationFrame(updateCSS);
        };

        // Drag End
        const onDragEnd = (e) => {
            if (!state.isDragging) return;
            state.isDragging = false;

            // Check for Click vs Drag
            // If movement was small and time was short, treat as click
            const now = Date.now();
            if (now - state.startDragTime < 200) {
                toggleZen();
            }
        };

        // Bind Events
        orb.addEventListener('mousedown', onDragStart);
        orb.addEventListener('touchstart', onDragStart, { passive: false });

        window.addEventListener('mousemove', onDragMove);
        window.addEventListener('touchmove', onDragMove, { passive: false });

        window.addEventListener('mouseup', onDragEnd);
        window.addEventListener('touchend', onDragEnd);
    }

    // Initialize
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Handle Navigation (Keep it alive/reset if needed)
    // Actually, since it's append to body, it might persist?
    // MKDocs instant loading replaces body CONTENT usually.
    // Let's re-run init on pageshow just in case.
    window.addEventListener('pageshow', () => {
        // If element is gone, re-create
        init();
    });

})();
