// Interceptor universal de alert para Tienda en Línea
if (typeof Swal !== 'undefined' && !window._nativeAlert) {
    window._nativeAlert = window.alert;
    window.alert = function(msg) {
        let icon = 'info';
        let cleanMsg = String(msg || '');
        if (cleanMsg.includes('¡') || cleanMsg.toLowerCase().includes('éxito') || cleanMsg.toLowerCase().includes('exito')) {
            icon = 'success';
        } else if (cleanMsg.toLowerCase().includes('error') || cleanMsg.toLowerCase().includes('problema') || cleanMsg.toLowerCase().includes('vacío')) {
            icon = 'warning';
        }
        Swal.fire({
            title: icon === 'success' ? '¡Excelente!' : (icon === 'warning' ? 'Aviso' : 'Información'),
            text: cleanMsg,
            icon: icon,
            confirmButtonText: 'Aceptar',
            confirmButtonColor: '#e11d48'
        });
    };
}

document.addEventListener('DOMContentLoaded', () => {
    // --- State ---
    let cart = [];
    const cartBadge = document.getElementById('cart-badge');
    const cartSidebar = document.getElementById('cart-sidebar');
    const cartItemsContainer = document.getElementById('cart-items-container');
    const cartTotal = document.getElementById('cart-total');
    
    const checkoutModal = document.getElementById('checkout-modal');
    
    // --- Slider Logic ---
    const slides = document.querySelectorAll('.slide');
    const hero = document.querySelector('.hero-slider');
    const slideToggle = document.getElementById('toggle-slides');
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    let currentSlide = 0;
    let autoplay = !reducedMotion.matches;
    
    function showSlide(index) {
        slides.forEach((slide, position) => {
            const active = position === index;
            slide.classList.toggle('active', active);
            slide.inert = !active;
        });
    }
    
    function nextSlide() {
        currentSlide = (currentSlide + 1) % slides.length;
        showSlide(currentSlide);
    }
    
    function prevSlide() {
        currentSlide = (currentSlide - 1 + slides.length) % slides.length;
        showSlide(currentSlide);
    }
    
    document.getElementById('next-slide').addEventListener('click', nextSlide);
    document.getElementById('prev-slide').addEventListener('click', prevSlide);
    
    function updateSlideToggle() {
        slideToggle.textContent = autoplay ? 'Ⅱ' : '▶';
        slideToggle.setAttribute('aria-label', autoplay ? 'Pausar la portada' : 'Reproducir la portada');
    }

    slideToggle.addEventListener('click', () => {
        autoplay = !autoplay;
        updateSlideToggle();
    });
    reducedMotion.addEventListener('change', event => {
        autoplay = !event.matches;
        updateSlideToggle();
    });
    showSlide(0);
    updateSlideToggle();
    setInterval(() => {
        if (autoplay && !document.hidden && !hero.matches(':hover, :focus-within')) nextSlide();
    }, 6500);

    // --- Actions ---
    function updateCartUI() {
        cartBadge.innerText = cart.length;
        cartItemsContainer.innerHTML = '';
        let total = 0;

        cart.forEach((item, index) => {
            total += item.price;
            cartItemsContainer.innerHTML += `
                <div class="cart-item">
                    <div class="cart-item-info">
                        <h4>${item.name}</h4>
                        <div class="cart-item-price">C$${item.price.toFixed(2)}</div>
                    </div>
                    <button class="close-cart" onclick="removeFromCart(${index})" style="font-size:1rem">&times;</button>
                </div>
            `;
        });
        
        cartTotal.innerText = `C$${total.toFixed(2)}`;
    }

    window.addToCart = function(id, name, price, stock) {
        const countInCart = cart.filter(item => item.id === id).length;
        if (countInCart >= stock) {
            alert('¡Lo sentimos! Ya no hay más stock disponible para este repuesto.');
            return;
        }
        cart.push({ id, name, price });
        updateCartUI();
        cartSidebar.classList.add('open');
    }

    window.removeFromCart = function(index) {
        cart.splice(index, 1);
        updateCartUI();
    }

    // --- UI Listeners ---
    // Cart Toggle
    document.getElementById('cart-icon').addEventListener('click', () => {
        cartSidebar.classList.add('open');
    });
    document.getElementById('close-cart-btn').addEventListener('click', () => {
        cartSidebar.classList.remove('open');
    });

    // Modals Open
    document.getElementById('btn-checkout-cart').addEventListener('click', () => {
        if(cart.length === 0) return alert('El carrito está vacío');
        cartSidebar.classList.remove('open');
        checkoutModal.classList.add('active');
        document.getElementById('checkout-form-view').style.display = 'block';
        document.getElementById('checkout-success-view').style.display = 'none';
    });

    // Modals Close
    document.querySelectorAll('.modal-close, .modal-overlay').forEach(el => {
        el.addEventListener('click', (e) => {
            if(e.target === el) {
                checkoutModal.classList.remove('active');
            }
        });
    });

    let lastOrder = null;

    // Simulate Checkout Form Submit
    document.getElementById('form-checkout').addEventListener('submit', (e) => {
        e.preventDefault();
        
        // Group items for the backend
        const groupedItems = [];
        cart.forEach(item => {
            let existing = groupedItems.find(i => i.producto_id === item.id);
            if (existing) {
                existing.cantidad += 1;
            } else {
                groupedItems.push({ producto_id: item.id, cantidad: 1 });
            }
        });

        const methodEl = document.getElementById('checkout-method');
        const phoneEl = document.getElementById('checkout-phone');

        const formaEntrega = 'Retiro en Tienda';
        const metodoPago = methodEl ? methodEl.value : 'Efectivo';
        const telefonoVal = phoneEl ? phoneEl.value.trim() : '';
        const direccionVal = 'Retiro en Tienda (Sucursal Masatepe)';

        // Guardar detalles de la orden antes de limpiar el carrito
        let total = cart.reduce((sum, item) => sum + item.price, 0);
        lastOrder = {
            items: [...cart],
            backend_items: groupedItems,
            total: total,
            date: new Date().toLocaleString(),
            name: document.getElementById('checkout-name').value.trim(),
            email: document.getElementById('checkout-email').value.trim(),
            phone: telefonoVal,
            address: direccionVal,
            delivery: formaEntrega,
            method: metodoPago
        };

        const botonEnviar = e.currentTarget.querySelector('[type=submit]');
        if (botonEnviar.disabled) return;
        botonEnviar.disabled = true;

        // Realizar la petición real al backend
        fetch('/api/ventas_web', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                nombre_cliente: lastOrder.name,
                email: lastOrder.email,
                telefono: lastOrder.phone,
                direccion: lastOrder.address,
                direccion_entrega: lastOrder.address,
                forma_entrega: lastOrder.delivery,
                metodo: lastOrder.method,
                items: lastOrder.backend_items
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                document.getElementById('checkout-form-view').style.display = 'none';
                document.getElementById('checkout-success-view').style.display = 'block';
                cart = []; // clear cart
                updateCartUI();
            } else {
                alert("Hubo un problema al procesar el pedido: " + (data.error || 'Desconocido'));
            }
        })
        .catch(error => {
            console.error("Error al registrar venta web:", error);
            alert("Error de conexión al procesar el pedido.");
        })
        .finally(() => { botonEnviar.disabled = false; });
    });

    window.imprimirFactura = function() {
        if (!lastOrder || lastOrder.items.length === 0) {
            alert('No hay detalles de la orden para imprimir.');
            return;
        }

        const printWindow = window.open('', '_blank');
        
        let itemsHtml = lastOrder.items.map(item => `
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">${item.name}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">C$${item.price.toFixed(2)}</td>
            </tr>
        `).join('');

        const html = `
            <html>
            <head>
                <title>Resumen de pedido - Jehová Jireh</title>
                <style>
                    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; padding: 40px; }
                    .header { text-align: center; margin-bottom: 40px; border-bottom: 2px solid #f97316; padding-bottom: 20px; }
                    .header h1 { color: #f97316; margin: 0 0 10px 0; font-size: 28px; }
                    .header p { margin: 5px 0; color: #666; }
                    .info-section { display: flex; justify-content: space-between; margin-bottom: 30px; }
                    .info-box { background: #f9f9f9; padding: 15px; border-radius: 8px; width: 45%; }
                    .info-box h3 { margin-top: 0; color: #444; font-size: 14px; text-transform: uppercase; border-bottom: 1px solid #ccc; padding-bottom: 5px; }
                    .info-box p { margin: 5px 0; font-size: 14px; }
                    table { width: 100%; border-collapse: collapse; margin-bottom: 30px; }
                    th { background-color: #0f172a; color: white; padding: 12px 10px; text-align: left; }
                    th.right { text-align: right; }
                    .total-row { font-size: 18px; font-weight: bold; text-align: right; }
                    .footer { text-align: center; color: #888; font-size: 12px; margin-top: 50px; border-top: 1px solid #ddd; padding-top: 20px; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>JEHOVÁ JIREH MASATEPE</h1>
                    <p>Moto Repuestos - ¡Nuestro prestigio es la calidad!</p>
                    <p>Resumen de pedido · Pendiente de pago</p>
                </div>
                
                <div class="info-section">
                    <div class="info-box">
                        <h3>Datos del Cliente</h3>
                        <p><strong>Nombre:</strong> ${lastOrder.name}</p>
                        <p><strong>Correo:</strong> ${lastOrder.email}</p>
                        <p><strong>Teléfono:</strong> ${lastOrder.phone || 'N/A'}</p>
                        <p><strong>Lugar de retiro:</strong> ${lastOrder.address}</p>
                    </div>
                    <div class="info-box">
                        <h3>Detalles de la Orden</h3>
                        <p><strong>Fecha:</strong> ${lastOrder.date}</p>
                        <p><strong>Forma de Entrega:</strong> ${lastOrder.delivery || 'Retiro en Tienda'}</p>
                        <p><strong>Método de Pago:</strong> ${lastOrder.method || 'Efectivo'}</p>
                    </div>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>Producto</th>
                            <th class="right">Precio</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${itemsHtml}
                        <tr>
                            <td style="padding: 15px 10px; text-align: right; font-weight: bold; font-size: 16px;">TOTAL A PAGAR:</td>
                            <td style="padding: 15px 10px; text-align: right; font-weight: bold; font-size: 16px; color: #f97316;">C$${lastOrder.total.toFixed(2)}</td>
                        </tr>
                    </tbody>
                </table>
                
                <div class="footer">
                    <p>Gracias por su preferencia. Si tiene alguna duda con su pedido, comuníquese al +505 8185 7270.</p>
                </div>
                
                <script>
                    // Esperar a que renderice y abrir ventana de impresión automáticamente
                    window.onload = function() { window.print(); }
                </script>
            </body>
            </html>
        `;
        
        printWindow.document.open();
        printWindow.document.write(html);
        printWindow.document.close();
    };

    // Simulate Register Password Form Submit (Hybrid strategy part 2)
    const hybridForm = document.getElementById('form-hybrid-register');
    if (hybridForm) {
        hybridForm.addEventListener('submit', (e) => {
            e.preventDefault();
            alert('¡Cuenta creada exitosamente! La próxima vez podrás rastrear tus pedidos.');
            checkoutModal.classList.remove('active');
        });
    }
    const zoneCategories = {
        frenos: ['Llantas', 'Frenos', 'Llantas y Cámaras', 'Sistema de Frenos'],
        motor: ['Motor', 'Motor y Partes Internas', 'Carburación y Combustible'],
        controles: ['Eléctrico', 'Sistema Eléctrico y Encendido', 'Cables y Controles'],
        transmision: ['Transmisión', 'Transmisión y Embrague']
    };
    // Algunos repuestos se buscan por una zona distinta a su categoría comercial.
    const zonePartNames = {
        frenos: /\bcables? de frenos?\b/i,
        motor: /\bbuj[ií]as?\b/i,
        controles: /\b(?:retrovisor(?:es)?|manetas?|puños?|manubrios?)\b/i
    };
    const explorer = document.querySelector('.moto-explorer');
    const zoneButtons = explorer.querySelectorAll('[data-zone]');
    const cards = document.querySelectorAll('.product-card');
    const results = document.getElementById('moto-results');
    const empty = document.getElementById('catalog-empty');
    const catalogTitle = document.getElementById('catalogo');
    const motoViews = explorer.querySelectorAll('[data-moto-view]');
    const motoDots = explorer.querySelectorAll('[data-moto-index]');
    const compatibility = document.getElementById('moto-compatibility');
    const compatibilityLabel = document.getElementById('moto-compatibility-label');
    const motoModelName = document.getElementById('moto-model-name');
    const defaultEmpty = document.getElementById('catalog-default-empty');
    const catalogModels = {
        ns200: /(?:bajaj[ -]*)?(?:pulsar[ -]*)?ns[ -]*200/,
        cg150: /(?:honda[ -]*)?cg[ -]*150/,
        ybr125: /(?:yamaha[ -]*)?ybr[ -]*125/,
        xr150l: /(?:honda[ -]*)?xr[ -]*150[ -]*l/,
        pulsar135: /(?:bajaj[ -]*)?pulsar[ -]*135(?:[ -]*ls)?/,
        cg125: /(?:honda[ -]*)?cg[ -]*125/,
        gxt200: /gxt[ -]*200/,
        gn125: /(?:suzuki[ -]*)?gn[ -]*125(?:[ -]*h)?/,
        tt150: /(?:akt[ -]*)?(?:tt[ -]*150|150[ -]*tt)/
    };
    const modelMatchers = Object.fromEntries(Object.entries(catalogModels).map(([id, model]) => [
        id, {
            registered: new RegExp(`^${model.source}$`, 'i'),
            mentioned: new RegExp(`\\b${model.source}\\b`, 'i')
        }
    ]));
    if (explorer.hasAttribute('data-feria-demo')) {
        modelMatchers.xr150l.mentioned = /\b(?:honda[ -]*)?xr[ -]*150(?:[ -]*l)?\b/i;
    }
    const cardDetails = Array.from(cards, card => {
        const name = card.querySelector('.card-title').textContent;
        const models = card.dataset.compatibility.split(/[/,;|\n]+/).map(value => value.trim()).filter(Boolean);
        const matches = new Map();
        motoViews.forEach(({dataset: {modelId}}) => {
            const matcher = modelMatchers[modelId];
            if (models.some(model => matcher.registered.test(model))) {
                matches.set(modelId, card.dataset.fitmentSource === 'Nombre del catálogo' ? 'catalog' : 'registered');
            }
            else if (models.length === 0 && matcher.mentioned.test(name)) matches.set(modelId, 'mentioned');
            else if (modelId === 'xr150l' && card.hasAttribute('data-xr150-referencia') &&
                     (models.length === 0 || models.includes('XR150'))) {
                matches.set(modelId, 'reference');
            }
        });
        return {card, name, matches, fitment: card.querySelector('.product-fitment')};
    });
    const unmatchedButton = document.getElementById('moto-unmatched');
    let motoIndex = 0;
    let categories = null;
    let selectedZone = 'all';
    let unmatchedOnly = false;

    function updateModelLabels() {
        const {modelName} = motoViews[motoIndex].dataset;
        motoModelName.textContent = modelName;
        compatibilityLabel.textContent = `Buscar repuestos para ${modelName}`;
    }

    function showMoto(index) {
        const direction = Math.sign(index - motoIndex);
        const nextIndex = (index + motoViews.length) % motoViews.length;
        if (nextIndex === motoIndex) return;
        motoViews[motoIndex].hidden = true;
        motoDots[motoIndex].setAttribute('aria-pressed', 'false');
        motoIndex = nextIndex;
        const view = motoViews[motoIndex];
        view.style.setProperty('--moto-entry', `${direction * 22}px`);
        view.hidden = false;
        motoDots[motoIndex].setAttribute('aria-pressed', 'true');
        updateModelLabels();
        if (compatibility.checked) filterCatalog();
    }

    explorer.querySelectorAll('[data-moto-step]').forEach(button => {
        button.addEventListener('click', () => showMoto(motoIndex + Number(button.dataset.motoStep)));
    });

    motoDots.forEach((button, index) => {
        button.addEventListener('click', () => showMoto(index));
    });

    function filterCatalog(animate = true) {
        const {modelId, modelName} = motoViews[motoIndex].dataset;
        let count = 0;
        cardDetails.forEach(({card, name, fitment, matches}) => {
            const inSelection = categories === null || categories.includes(card.dataset.category)
                || Boolean(zonePartNames[selectedZone]?.test(name));
            const match = matches.get(modelId);
            const visible = unmatchedOnly ? matches.size === 0 : inSelection && (!compatibility.checked || Boolean(match));
            card.hidden = !visible;
            fitment.hidden = !visible || !compatibility.checked;
            if (!fitment.hidden) {
                fitment.textContent = match === 'registered'
                    ? 'Compatibilidad registrada en el catálogo'
                    : match === 'catalog'
                        ? 'Modelo indicado en el catálogo · Confirma año y versión'
                    : match === 'reference'
                        ? 'Referencia para XR150 · Confirma la versión de tu moto'
                        : 'El nombre menciona el modelo · Confirma la versión antes de comprar';
            }
            if (visible && animate && !reducedMotion.matches && count < 6) {
                card.getAnimations().filter(animation => animation.id === 'catalog-entry')
                    .forEach(animation => animation.cancel());
                card.animate([{opacity: 0.55, translate: '0 8px'}, {opacity: 1, translate: '0 0'}],
                    {id: 'catalog-entry', duration: 220, delay: count * 22, easing: 'ease-out'});
            }
            count += Number(visible);
        });
        zoneButtons.forEach(button => {
            button.setAttribute('aria-pressed', String(button.dataset.zone === selectedZone));
        });
        const scope = categories === null ? 'en el catálogo' : 'en esta selección';
        const countText = `${count} ${count === 1 ? 'repuesto' : 'repuestos'}`;
        const noMatches = `Sin coincidencias disponibles para ${modelName} ${scope}.`;
        results.textContent = unmatchedOnly ? `${countText} fuera de los modelos del carrusel` : compatibility.checked
            ? (count === 0 ? noMatches : `${countText} encontrados para ${modelName} ${scope}`)
            : `${countText} ${scope} · Compatibilidad sin filtrar`;
        unmatchedButton.setAttribute('aria-pressed', String(unmatchedOnly));
        catalogTitle.textContent = unmatchedOnly ? 'Repuestos fuera del carrusel' : 'Nuestro Catálogo';
        const filtered = unmatchedOnly || categories !== null || compatibility.checked;
        empty.hidden = count > 0 || !filtered;
        if (!empty.hidden) {
            empty.textContent = unmatchedOnly ? 'Todos los repuestos disponibles tienen alguna coincidencia en el carrusel.' : compatibility.checked
                ? `${noMatches} Puedes probar otra zona o desactivar el filtro de compatibilidad.`
                : 'No hay repuestos en esta selección. Prueba otra zona.';
        }
        if (defaultEmpty) defaultEmpty.hidden = filtered;
    }

    zoneButtons.forEach(button => {
        button.addEventListener('click', () => {
            unmatchedOnly = false;
            selectedZone = button.dataset.zone;
            categories = zoneCategories[selectedZone] ?? null;
            filterCatalog();
        });
    });

    const categoryToggle = document.getElementById('category-menu-toggle');
    const categoryMenu = document.getElementById('category-menu');

    function fitCategoryMenu() {
        if (!categoryMenu.hidden) {
            const top = categoryMenu.getBoundingClientRect().top;
            categoryMenu.style.setProperty('--category-menu-top', `${top}px`);
        }
    }

    function setCategoryMenuOpen(open) {
        categoryMenu.hidden = !open;
        categoryToggle.setAttribute('aria-expanded', String(open));
        fitCategoryMenu();
    }

    categoryToggle.addEventListener('click', () => setCategoryMenuOpen(categoryMenu.hidden));
    window.addEventListener('resize', fitCategoryMenu);
    document.addEventListener('click', event => {
        if (!categoryMenu.hidden && !categoryToggle.parentElement.contains(event.target)) {
            setCategoryMenuOpen(false);
        }
    });
    document.addEventListener('keydown', event => {
        if (event.key === 'Escape' && !categoryMenu.hidden) {
            setCategoryMenuOpen(false);
            categoryToggle.focus();
        }
    });

    categoryMenu.querySelectorAll('.filter-btn').forEach(button => {
        button.addEventListener('click', event => {
            event.preventDefault();
            unmatchedOnly = false;
            const category = button.dataset.filter;
            categories = category === 'all' ? null : [category];
            selectedZone = category === 'all' ? 'all' : null;
            if (category === 'all') compatibility.checked = false;
            filterCatalog();
            setCategoryMenuOpen(false);
            catalogTitle.focus({preventScroll: true});
            catalogTitle.scrollIntoView();
        });
    });

    compatibility.addEventListener('change', () => {
        unmatchedOnly = false;
        filterCatalog();
    });
    unmatchedButton.addEventListener('click', () => {
        unmatchedOnly = !unmatchedOnly;
        compatibility.checked = false;
        categories = null;
        selectedZone = unmatchedOnly ? null : 'all';
        filterCatalog();
        catalogTitle.focus();
        catalogTitle.scrollIntoView();
    });
    updateModelLabels();
    filterCatalog(false);
    explorer.hidden = false;
});
