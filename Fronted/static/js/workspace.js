/* Navigation presentation only: existing module handlers continue to own their data. */
document.addEventListener('DOMContentLoaded', () => {
    const root = document.body;
    const toggle = document.getElementById('sidebar-toggle');
    const sidebar = document.getElementById('workspace-sidebar');
    const backdrop = document.getElementById('sidebar-backdrop');
    if (!toggle || !sidebar || !backdrop) return;
    const mobile = window.matchMedia('(max-width: 768px)');
    const updateToggle = () => {
        const open = mobile.matches ? root.classList.contains('sidebar-open') : !root.classList.contains('sidebar-collapsed');
        toggle.setAttribute('aria-expanded', String(open));
        toggle.setAttribute('aria-label', open ? 'Cerrar menú' : 'Abrir menú');
        backdrop.hidden = !mobile.matches || !open;
        sidebar.inert = mobile.matches && !open;
    };
    const closeMobile = () => { root.classList.remove('sidebar-open'); updateToggle(); };
    toggle.addEventListener('click', () => {
        root.classList.toggle(mobile.matches ? 'sidebar-open' : 'sidebar-collapsed');
        if (mobile.matches) root.classList.remove('sidebar-collapsed');
        updateToggle();
    });
    backdrop.addEventListener('click', closeMobile);
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && root.classList.contains('sidebar-open')) { closeMobile(); toggle.focus(); }
    });
    mobile.addEventListener('change', () => { root.classList.remove('sidebar-open', 'sidebar-collapsed'); updateToggle(); });
    sidebar.querySelectorAll('.nav-item').forEach(link => {
        link.title = link.textContent.trim();
        link.addEventListener('click', () => { if (mobile.matches) closeMobile(); });
    });

    const financeLink = sidebar.querySelector('[data-tab="tab-finanzas"]');
    const financeButtons = [...document.querySelectorAll('#tab-finanzas .subtabs-container > button')];
    let subnav;
    if (financeLink && financeButtons.length) {
        subnav = document.createElement('div');
        subnav.className = 'shell-subnav';
        subnav.setAttribute('aria-label', 'Secciones de Estados Financieros');
        financeLink.after(subnav);
        financeButtons.forEach(source => {
            const button = document.createElement('button');
            button.type = 'button';
            button.textContent = source.textContent.trim();
            button.addEventListener('click', () => { source.click(); syncSubnav(); if (mobile.matches) closeMobile(); });
            source.addEventListener('click', () => queueMicrotask(syncSubnav));
            subnav.append(button);
        });
    }
    function syncSubnav() {
        if (!subnav) return;
        subnav.hidden = !document.getElementById('tab-finanzas')?.classList.contains('active');
        [...subnav.children].forEach((button, i) => {
            const active = financeButtons[i].classList.contains('active');
            button.classList.toggle('active', active);
            if (active) button.setAttribute('aria-current', 'page'); else button.removeAttribute('aria-current');
        });
    }
    window.addEventListener('workspace:tab-change', event => {
        window.scrollTo({ top: 0, behavior: 'instant' });
        sidebar.querySelectorAll('.nav-item').forEach(link => {
            if (link.dataset.tab === event.detail.tabId) link.setAttribute('aria-current', 'page');
            else link.removeAttribute('aria-current');
        });
        syncSubnav();
    });
    updateToggle();
    syncSubnav();

    const accountBody = document.getElementById('tbody-cuentas');
    const accountSearch = document.getElementById('shell-account-search');
    const accountClass = document.getElementById('shell-account-class');
    const previous = document.getElementById('shell-account-prev');
    const next = document.getElementById('shell-account-next');
    if (accountBody && accountSearch && accountClass && previous && next) {
        let page = 1;
        const normalize = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
        function renderAccounts() {
            const rows = [...accountBody.rows].filter(row => row.cells.length >= 4);
            const term = normalize(accountSearch.value.trim());
            const matches = rows.filter(row => normalize(row.textContent).includes(term) &&
                (!accountClass.value || row.cells[2].textContent.trim() === accountClass.value));
            const pages = Math.max(1, Math.ceil(matches.length / 10));
            page = Math.min(page, pages);
            rows.forEach(row => { row.hidden = true; });
            matches.slice((page - 1) * 10, page * 10).forEach(row => { row.hidden = false; });
            document.getElementById('shell-account-count').textContent = matches.length
                ? `Mostrando ${(page - 1) * 10 + 1} a ${Math.min(page * 10, matches.length)} de ${matches.length} cuentas`
                : 'No hay cuentas que coincidan con la búsqueda.';
            document.getElementById('shell-account-page').textContent = `${page} / ${pages}`;
            previous.disabled = page <= 1;
            next.disabled = page >= pages;
        }
        const refreshAccounts = () => {
            const selected = accountClass.value;
            const classifications = [...new Set([...accountBody.rows].filter(row => row.cells.length >= 4)
                .map(row => row.cells[2].textContent.trim()))].sort();
            accountClass.replaceChildren(new Option('Todas las clasificaciones', ''), ...classifications.map(value => new Option(value, value)));
            if (classifications.includes(selected)) accountClass.value = selected;
            page = 1;
            renderAccounts();
        };
        new MutationObserver(refreshAccounts).observe(accountBody, { childList: true });
        accountSearch.addEventListener('input', () => { page = 1; renderAccounts(); });
        accountClass.addEventListener('change', () => { page = 1; renderAccounts(); });
        previous.addEventListener('click', () => { page--; renderAccounts(); });
        next.addEventListener('click', () => { page++; renderAccounts(); });
        refreshAccounts();
    }
});
