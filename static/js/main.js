// Initialize tooltips
document.addEventListener('DOMContentLoaded', function() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// Activate current nav item based on URL
document.addEventListener('DOMContentLoaded', function() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        // Get the href attribute
        const href = link.getAttribute('href');
        
        // Check if the current path starts with the href (excluding the root path)
        if (href !== '/' && currentPath.startsWith(href)) {
            link.classList.add('active');
        } else if (href === '/' && currentPath === '/') {
            link.classList.add('active');
        }
    });
});

// Add to cart functionality
function addToCart(productId, quantityInput) {
    const quantity = document.getElementById(quantityInput).value;
    
    // Create form data
    const formData = new FormData();
    formData.append('product_id', productId);
    formData.append('quantity', quantity);
    formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
    
    // Send AJAX request
    fetch('/cart/add/' + productId + '/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-success alert-dismissible fade show';
            alertDiv.setAttribute('role', 'alert');
            alertDiv.innerHTML = data.message + '<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>';
            
            document.querySelector('.messages').appendChild(alertDiv);
            
            // Update cart counter
            document.getElementById('cart-counter').innerText = data.cart_count;
        }
    })
    .catch(error => console.error('Error:', error));
}

// Update product quantity in cart
function updateCartQuantity(productId, element) {
    const quantity = element.value;
    
    // Create form data
    const formData = new FormData();
    formData.append('product_id', productId);
    formData.append('quantity', quantity);
    formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
    
    // Send AJAX request
    fetch('/cart/update/', {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update total price
            document.getElementById('cart-total').innerText = data.total_price;
            document.getElementById('item-total-' + productId).innerText = data.item_total;
        }
    })
    .catch(error => console.error('Error:', error));
}

// Filter products based on category
function filterProducts(categoryId) {
    // Get all product cards
    const productCards = document.querySelectorAll('.product-item');
    
    // Show/hide products based on category
    productCards.forEach(card => {
        if (categoryId === 'all' || card.dataset.category === categoryId) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

// Dynamic form fields
function addFormField(formsetName) {
    const totalForms = document.getElementById(`id_${formsetName}-TOTAL_FORMS`);
    const formCount = parseInt(totalForms.value);
    const row = document.getElementById(`${formsetName}-empty`).cloneNode(true);
    
    row.id = `${formsetName}-${formCount}`;
    row.style.display = 'block';
    
    // Replace __prefix__ with the actual form count
    row.innerHTML = row.innerHTML.replace(/__prefix__/g, formCount);
    
    // Add the new form before the "add" button
    document.getElementById(`${formsetName}-add-btn`).parentNode.insertBefore(row, document.getElementById(`${formsetName}-add-btn`));
    
    // Increment the form count
    totalForms.value = formCount + 1;
}

// Delete form field
function deleteFormField(formsetName, index) {
    document.getElementById(`${formsetName}-${index}-DELETE`).checked = true;
    document.getElementById(`${formsetName}-${index}`).style.display = 'none';
}

// Calculate inventory difference
function calculateDifference() {
    const expected = parseFloat(document.getElementById('id_quantity_expected').value) || 0;
    const actual = parseFloat(document.getElementById('id_quantity_actual').value) || 0;
    const difference = actual - expected;
    
    document.getElementById('inventory-difference').innerText = difference;
    
    // Set color based on value
    if (difference < 0) {
        document.getElementById('inventory-difference').className = 'text-danger';
    } else if (difference > 0) {
        document.getElementById('inventory-difference').className = 'text-success';
    } else {
        document.getElementById('inventory-difference').className = 'text-muted';
    }
}

// Format currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('uk-UA', {
        style: 'currency',
        currency: 'UAH'
    }).format(amount);
}

// Print element
function printElement(elementId) {
    const element = document.getElementById(elementId);
    const originalDisplay = element.style.display;
    
    const printContent = document.createElement('div');
    printContent.innerHTML = element.innerHTML;
    
    document.body.innerHTML = printContent.innerHTML;
    window.print();
    
    location.reload();
} 