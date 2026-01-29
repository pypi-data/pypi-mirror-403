/**
 * CINEMATIC ACCESSIBILITY
 * ----------------------------------------------------------------------------
 * Ensures the theme remains usable for all audiences.
 */

(function () {
    'use strict';

    function enhanceFocusVisibility() {
        // Cinematic themes often lose focus rings in favor of aesthetics.
        // We enforce them via JS if needed, or just allow CSS users.
        // This script ensures that keyboard users have a class applied.

        document.body.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                document.body.classList.add('user-is-tabbing');
            }
        });

        document.body.addEventListener('mousedown', () => {
            document.body.classList.remove('user-is-tabbing');
        });
    }

    function checkContrast() {
        // Runtime check could go here if we wanted to enforce WCAG
        // For now, this is a placeholder for future tooling.
    }

    enhanceFocusVisibility();

    // Expose for debug
    window.CinematicA11y = {
        check: checkContrast
    };

})();
