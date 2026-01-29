/**
 * CINEMATIC INTERACTION ENGINE
 * ----------------------------------------------------------------------------
 * Cinematographer: Motion & Camera
 */

(function () {
    'use strict';

    // Configuration
    const CONFIG = {
        revealThreshold: 0.15, // Trigger when 15% visible
        parallaxStrength: 15 // pixels of movement
    };

    /**
     * SCROLL REVEAL OBSERVER
     * Watches elements to trigger entrance animations.
     */
    function setupScrollReveals() {
        // Select targets: Headings, Images, Code Blocks, Admonitions
        const targets = document.querySelectorAll(
            '.md-typeset h1, .md-typeset h2, .md-typeset h3, ' +
            '.md-typeset p > img, .md-typeset pre, .md-typeset .admonition, ' +
            '.md-button'
        );

        const observerConfig = {
            root: null,
            rootMargin: '0px',
            threshold: CONFIG.revealThreshold
        };

        const revealObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    // Add entrance class
                    entry.target.classList.add('cinema-fade-up');

                    // Stop observing once revealed
                    observer.unobserve(entry.target);
                }
            });
        }, observerConfig);

        targets.forEach(target => {
            // Set initial state via style to avoid FOUC before class addition?
            // CSS handles opacity: 0 for .cinema-fade-up start, but we need
            // to ensure they are hidden BEFORE the class is added if we want
            // the animation to play. 
            // 
            // ACTUALLY: The CSS class `.cinema-fade-up` has the animation 
            // which goes from 0 to 1. 
            // If we want them hidden initially, we need a helper class or 
            // just add the class 'cinema-hidden' then swap it.
            //
            // SIMPLIFICATION: We simply add the animation class. 
            // However, to prevent them from being visible *before* scroll,
            // we'd need to style them initially. 
            // 
            // REVISED STRATEGY: We don't hide *everything* by default (SEO/UX risk).
            // We only animate specific impactful elements.

            revealObserver.observe(target);
        });
    }

    /**
     * PARALLAX ENGINE
     * Subtle mouse-based movement for the "Camera Shake" feel.
     */
    function setupParallax() {
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

        // Target specific depth layers if they existed. 
        // Since we don't have a multi-plane scene, we'll apply it 
        // to the BACKGROUND GRAIN to make it feel like it's on a lens 
        // separate from the content.

        // We can also parallax the main content slightly against the scroll.

        const grain = document.querySelector('.film-grain');

        if (grain) {
            document.addEventListener('mousemove', (e) => {
                const x = (window.innerWidth - e.pageX * 2) / 100;
                const y = (window.innerHeight - e.pageY * 2) / 100;

                // Very subtle movement
                grain.style.transform = `translate(${x}px, ${y}px)`;
            });
        }
    }

    /**
     * MAGNETIC BUTTONS (Optional Polish)
     */
    function setupMagneticButtons() {
        const buttons = document.querySelectorAll('.md-button--primary');

        buttons.forEach(btn => {
            btn.addEventListener('mousemove', (e) => {
                const rect = btn.getBoundingClientRect();
                const x = e.clientX - rect.left - rect.width / 2;
                const y = e.clientY - rect.top - rect.height / 2;

                // Strength
                btn.style.transform = `translate(${x * 0.2}px, ${y * 0.2}px)`;
            });

            btn.addEventListener('mouseleave', () => {
                btn.style.transform = 'translate(0px, 0px)';
            });
        });
    }

    /**
     * INIT
     */
    function initInteractions() {
        console.log('🎬 Initializing Motion Engine...');

        requestAnimationFrame(() => {
            setupScrollReveals();
            setupParallax();
            setupMagneticButtons();
        });
    }

    // Hook into Material's instant navigation 'document$' observable? 
    // Standard DOMContentLoaded is fine for first load.
    // We need to re-run on navigation.

    if (window.document$) {
        window.document$.subscribe(() => {
            // slight delay to wait for content
            setTimeout(initInteractions, 100);
        });
    } else {
        // Fallback
        document.addEventListener('DOMContentLoaded', initInteractions);
    }

})();
