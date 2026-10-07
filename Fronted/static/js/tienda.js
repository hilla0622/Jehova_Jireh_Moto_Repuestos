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
    let currentSlide = 0;
    
    function showSlide(index) {
        slides.forEach(s => s.classList.remove('active'));
        slides[index].classList.add('active');
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
    
    // Auto slide every 5 seconds
    setInterval(nextSlide, 5000);

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
                        <div class="cart-item-price">$${item.price.toFixed(2)}</div>
                    </div>
                    <button class="close-cart" onclick="removeFromCart(${index})" style="font-size:1rem">&times;</button>
                </div>
            `;
        });
        
        cartTotal.innerText = `$${total.toFixed(2)}`;
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

        // Guardar detalles de la orden antes de limpiar el carrito
        let total = cart.reduce((sum, item) => sum + item.price, 0);
        lastOrder = {
            items: [...cart],
            backend_items: groupedItems,
            total: total,
            date: new Date().toLocaleString(),
            name: document.getElementById('checkout-name').value,
            email: document.getElementById('checkout-email').value,
            address: document.getElementById('checkout-address').value
        };

        // Realizar la petición real al backend
        fetch('/api/ventas_web', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                nombre_cliente: lastOrder.name,
                email: lastOrder.email,
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
                alert("Hubo un problema al procesar el pedido: " + data.error);
            }
        })
        .catch(error => {
            console.error("Error al registrar venta web:", error);
            alert("Error de conexión al procesar el pedido.");
        });
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
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">$${item.price.toFixed(2)}</td>
            </tr>
        `).join('');

        const html = `
            <html>
            <head>
                <title>Factura - Jehová Jireh</title>
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
                    <p>Comprobante de Venta</p>
                </div>
                
                <div class="info-section">
                    <div class="info-box">
                        <h3>Datos del Cliente</h3>
                        <p><strong>Nombre:</strong> ${lastOrder.name}</p>
                        <p><strong>Correo:</strong> ${lastOrder.email}</p>
                        <p><strong>Dirección:</strong> ${lastOrder.address}</p>
                    </div>
                    <div class="info-box">
                        <h3>Detalles de la Orden</h3>
                        <p><strong>Fecha:</strong> ${lastOrder.date}</p>
                        <p><strong>Método de Pago:</strong> Contra Entrega / Web</p>
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
                            <td style="padding: 15px 10px; text-align: right; font-weight: bold; font-size: 16px; color: #f97316;">$${lastOrder.total.toFixed(2)}</td>
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
});


    // --- Filter Logic ---
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const filter = btn.getAttribute('data-filter');
            document.querySelectorAll('.product-card').forEach(card => {
                if (filter === 'all' || card.getAttribute('data-category') === filter) {
                    card.style.display = 'flex';
                } else {
                    card.style.display = 'none';
                }
            });
            document.querySelector('.catalog-container').scrollIntoView({behavior: 'smooth'});
        });
    });
