// Cinematic Projector Roll Controller

(function () {
    const DEBUG = false;
    const DURATION_OUT = 250;
    const DURATION_IN = 400; // Includes bounce

    // Target the content container, NOT the body
    let el;

    function getEl() {
        if (!el) el = document.querySelector('.md-container');
        return el;
    }

    function playOut(callback) {
        requestAnimationFrame(() => {
            getEl().classList.add('anim-active');
            getEl().classList.add('anim-roll-out');

            setTimeout(() => {
                callback();
            }, DURATION_OUT);
        });
    }

    function playIn() {
        getEl().classList.add('anim-active');
        getEl().classList.add('anim-roll-in');
        getEl().classList.remove('anim-roll-out');

        setTimeout(() => {
            getEl().classList.remove('anim-roll-in');

            setTimeout(() => {
                getEl().classList.remove('anim-active');
            }, 50);
        }, DURATION_IN);
    }

    document.addEventListener('click', (e) => {
        if (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey || e.button !== 0) return;

        let target = e.target;
        while (target && target.tagName !== 'A') {
            target = target.parentElement;
        }

        if (!target || !target.href) return;
        if (target.hostname !== window.location.hostname && target.hostname !== '') return;
        if (target.pathname === window.location.pathname && target.hash) return;
        if (target.href.match(/^mailto:/) || target.download) return;

        e.preventDefault();
        e.stopPropagation();

        playOut(() => {
            window.location.href = target.href;
        });
    }, true);


    document.addEventListener('DOMContentLoaded', () => {
        requestAnimationFrame(() => playIn());
    });

    window.addEventListener('pageshow', (event) => {
        if (event.persisted) {
            getEl().classList.remove('anim-roll-out');
            playIn();
        }
    });

})();
