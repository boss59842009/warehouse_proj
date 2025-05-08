// Функціонал сторінки створення замовлення
document.addEventListener('DOMContentLoaded', function() {
    // Знаходимо всі необхідні елементи
    const checkboxes = document.querySelectorAll('.check-item');
    const qtyInputs = document.querySelectorAll('.qty-input');
    const submitBtn = document.getElementById('submitBtn');
    const selectedCountEl = document.getElementById('selectedCount');
    const totalQuantityEl = document.getElementById('totalQuantity');
    const orderForm = document.getElementById('orderForm');
    const itemsJsonInput = document.getElementById('items_json');
    
    // Додаємо обробники подій для чекбоксів
    for (let i = 0; i < checkboxes.length; i++) {
        checkboxes[i].addEventListener('change', function() {
            const row = this.closest('tr');
            const qtyInput = row.querySelector('.qty-input');
            
            if (qtyInput) {
                qtyInput.disabled = !this.checked;
                if (this.checked) {
                    qtyInput.value = 1;
                }
            }
            
            updateCounters();
        });
    }
    
    // Додаємо обробники для полів кількості
    for (let i = 0; i < qtyInputs.length; i++) {
        qtyInputs[i].addEventListener('input', function() {
            const max = parseInt(this.getAttribute('max')) || 1;
            let value = parseInt(this.value) || 1;
            
            if (value < 1) value = 1;
            if (value > max) value = max;
            
            this.value = value;
            updateCounters();
        });
    }
    
    // Функція для підрахунку вибраних товарів і загальної кількості
    function updateCounters() {
        let selectedCount = 0;
        let totalQuantity = 0;
        
        for (let i = 0; i < checkboxes.length; i++) {
            if (checkboxes[i].checked) {
                selectedCount++;
                
                const row = checkboxes[i].closest('tr');
                const qtyInput = row.querySelector('.qty-input');
                
                if (qtyInput) {
                    totalQuantity += parseInt(qtyInput.value) || 1;
                }
            }
        }
        
        selectedCountEl.textContent = selectedCount;
        totalQuantityEl.textContent = totalQuantity;
        
        // Активуємо/деактивуємо кнопку
        if (selectedCount > 0) {
            submitBtn.disabled = false;
        } else {
            submitBtn.disabled = true;
        }
    }
    
    // Обробник для кнопки відправки форми
    if (submitBtn) {
        submitBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            const selectedItems = [];
            
            for (let i = 0; i < checkboxes.length; i++) {
                if (checkboxes[i].checked) {
                    const row = checkboxes[i].closest('tr');
                    const qtyInput = row.querySelector('.qty-input');
                    
                    selectedItems.push({
                        variation_id: checkboxes[i].value,
                        quantity: parseInt(qtyInput.value) || 1
                    });
                }
            }
            
            if (selectedItems.length === 0) {
                alert('Будь ласка, виберіть хоча б один товар для замовлення.');
                return;
            }
            
            itemsJsonInput.value = JSON.stringify(selectedItems);
            orderForm.submit();
        });
    }
    
    // Запускаємо перший підрахунок при завантаженні сторінки
    updateCounters();
}); 