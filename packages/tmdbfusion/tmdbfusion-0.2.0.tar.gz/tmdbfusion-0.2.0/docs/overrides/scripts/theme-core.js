/**
 * CINEMATIC THEME CORE
 * ----------------------------------------------------------------------------
 * Director: Main Entry & Lifecycle
 */

(function () {
    'use strict';

    // State Management
    const CinematicState = {
        isReady: false,
        currentTheme: 'default', // 'default' (light) or 'slate' (dark)
        reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches
    };

    /**
     * INJECT CINEMATIC LAYERS
     * Adds the Grain and Vignette divs dynamically to avoid polluting markdown.
     */
    function injectCinematicLayers() {
        const body = document.body;

        // Create Grain
        if (!document.querySelector('.film-grain')) {
            const grain = document.createElement('div');
            grain.className = 'film-grain';
            body.appendChild(grain);
        }

        // Create Vignette
        if (!document.querySelector('.vignette-overlay')) {
            const vignette = document.createElement('div');
            vignette.className = 'vignette-overlay';
            body.appendChild(vignette);
        }

        /* 
           Note: We do NOT inject scanlines by default as they can be distracting 
           for reading documentation. They are available via utility class if needed.
        */

        console.log('🎬 Cinematic Layers Injected');
    }

    /**
     * THEME SYNC
     * Listens for mkdocs-material theme changes to potentially trigger specifics.
     * (Most is handled by CSS, but this is for JS-driven canvas effects if added).
     */
    function setupThemeListener() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'data-md-color-scheme') {
                    const newScheme = document.body.getAttribute('data-md-color-scheme');
                    CinematicState.currentTheme = newScheme;
                    console.log(`🎬 Theme Switch: ${newScheme}`);
                    // Trigger custom event for other modules
                    window.dispatchEvent(new CustomEvent('cinematic:themechange', { detail: { theme: newScheme } }));
                }
            });
        });

        observer.observe(document.body, { attributes: true });
    }

    /**
     * INITIALIZATION
     */
    function init() {
        if (CinematicState.isReady) return;

        injectCinematicLayers();
        setupThemeListener();

        // Initial read
        CinematicState.currentTheme = document.body.getAttribute('data-md-color-scheme') || 'default';

        CinematicState.isReady = true;
        window.CinematicState = CinematicState; // Expose globally for other modules

        console.log('🎬 Cinematic Core Ready');
    }

    // MkDocs instant loading support
    // We hook into the DOMContentLoaded event but also mkdocs custom events if they existed.
    // Material handles navigation with instant loading, so we need to re-init some things.
    // Actually, 'document$' observable is the Material way, but vanilla Listeners work for base setup.

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
