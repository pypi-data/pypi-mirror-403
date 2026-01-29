/**
 * 🎬 CINEMATIC ENGINE - "The Projectionist"
 * --------------------------------------------------------------------------
 * Handles dynamic injection of cinematic artifacts and scroll-based
 * "Reveal" animations. Designed to be lightweight and defensive.
 */

(function () {
    'use strict';

    // Configuration
    const CONFIG = {
        grainClass: 'cine-grain-overlay',
        vignetteClass: 'cine-vignette-overlay',
        revealSelector: '.md-typeset h2, .md-typeset h3, .md-typeset blockquote, .md-typeset table, .md-typeset .admonition',
        revealClass: 'cine-reveal-active',
        hiddenClass: 'cine-reveal-hidden',
        threshold: 0.15 // Trigger when 15% visible
    };

    /**
     * 🏗️ Artifact Injector
     * Creates the grain and vignette overlays if they don't exist.
     */
    function injectArtifacts() {
        // Grain
        if (!document.querySelector(`.${CONFIG.grainClass}`)) {
            const grain = document.createElement('div');
            grain.className = CONFIG.grainClass;
            document.body.appendChild(grain);
        }
        // Vignette
        if (!document.querySelector(`.${CONFIG.vignetteClass}`)) {
            const vignette = document.createElement('div');
            vignette.className = CONFIG.vignetteClass;
            document.body.appendChild(vignette);
        }
    }

    /**
     * 👁️ Scroll Observer
     * Adds 'revealed' classes to elements as they enter the viewport.
     * Gives a sense of "Unfolding Narrative".
     */
    function setupScrollReveal() {
        // Respect reduced motion preferences
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            return;
        }

        const elements = document.querySelectorAll(CONFIG.revealSelector);

        // Initial state: hide them
        elements.forEach(el => {
            el.classList.add(CONFIG.hiddenClass);
        });

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add(CONFIG.revealClass);
                    entry.target.classList.remove(CONFIG.hiddenClass);
                    observer.unobserve(entry.target); // Play once
                }
            });
        }, {
            root: null,
            margin: '0px',
            threshold: CONFIG.threshold
        });

        elements.forEach(el => observer.observe(el));
    }

    /**
     * 🚀 Initialization
     * Runs on DOMContentLoaded and handles MkDocs instant navigation integration.
     */
    function init() {
        console.log("🎥 [Cinematic] Action.");
        injectArtifacts();
        setupScrollReveal();
    }

    // --- Boot Sequence ---

    // Standard load
    document.addEventListener('DOMContentLoaded', init);

    // MkDocs Material "Instant Loading" support
    // This event is fired when a new page is loaded via XHR
    if (typeof window.document$ !== 'undefined') {
        window.document$.subscribe(function () {
            // Re-run setup on navigation (MkDocs replaces content container)
            // We don't need to re-inject artifacts (they are on body), just re-observe
            console.log("🎥 [Cinematic] Cut to new scene.");
            setupScrollReveal();
        });
    }

})();
