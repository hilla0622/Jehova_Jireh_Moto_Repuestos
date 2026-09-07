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

    window.addToCart = function(name, price) {
        cart.push({ name, price });
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

    // Simulate Checkout Form Submit
    document.getElementById('form-checkout').addEventListener('submit', (e) => {
        e.preventDefault();
        // Hide form, show success (Hybrid strategy part 1)
        document.getElementById('checkout-form-view').style.display = 'none';
        document.getElementById('checkout-success-view').style.display = 'block';
        cart = []; // clear cart
        updateCartUI();
    });

    // Simulate Register Password Form Submit (Hybrid strategy part 2)
    document.getElementById('form-hybrid-register').addEventListener('submit', (e) => {
        e.preventDefault();
        alert('¡Cuenta creada exitosamente! La próxima vez podrás rastrear tus pedidos.');
        checkoutModal.classList.remove('active');
    });
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
