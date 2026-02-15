
(function () {
    const tabs = document.querySelectorAll('[data-tabs] .tab');
    const panels = document.querySelectorAll('[data-panel]');
    if (!tabs.length) return;

    function setActive(name) {
        tabs.forEach(t => t.classList.toggle('is-active', t.dataset.tab === name));
        panels.forEach(p => p.classList.toggle('is-active', p.dataset.panel === name));
    }

    tabs.forEach(btn => {
        btn.addEventListener('click', () => setActive(btn.dataset.tab));
    });
})();   