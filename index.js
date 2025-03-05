// Predefined products with initial prices (expanded list)
const predefinedProducts = {
    'Хлеб белый': 40,
    'Хлеб ржаной': 45,
    'Молоко 2.5%': 89,
    'Молоко 3.2%': 95,
    'Яйца С1': 85,
    'Яйца С0': 95,
    'Сыр российский': 320,
    'Сыр голландский': 340,
    'Масло сливочное': 150,
    'Масло подсолнечное': 120,
    'Говядина': 400,
    'Свинина': 380,
    'Курица': 280,
    'Минтай': 350,
    'Треска': 420,
    'Картофель': 45,
    'Морковь': 35,
    'Лук репчатый': 30,
    'Капуста': 25,
    'Огурцы': 180,
    'Помидоры': 220,
    'Яблоки': 130,
    'Бананы': 110,
    'Апельсины': 140,
    'Рис': 90,
    'Гречка': 85,
    'Макароны': 65,
    'Сахар': 55,
    'Соль': 20,
    'Чай черный': 160,
    'Кофе молотый': 450,
    'Печенье': 130,
    'Конфеты': 280,
    'Сметана': 140,
    'Творог': 190,
    'Кефир': 75
};

// Initialize shopping list from localStorage or empty array
let shoppingList = JSON.parse(localStorage.getItem('shoppingList')) || [];

// DOM Elements
const productSearch = document.getElementById('productSearch');
const searchResults = document.getElementById('searchResults');
const productList = document.getElementById('productList');
const totalPrice = document.getElementById('totalPrice');
const addProductBtn = document.getElementById('addProduct');
const refreshPricesBtn = document.getElementById('refreshPrices');
const clearListBtn = document.getElementById('clearList');

// Event Listeners
productSearch.addEventListener('input', handleSearch);
addProductBtn.addEventListener('click', handleAddProduct);
refreshPricesBtn.addEventListener('click', refreshPrices);
clearListBtn.addEventListener('click', clearList);

// Enhanced search functionality
function handleSearch(e) {
    const searchTerm = e.target.value.toLowerCase();
    if (!searchTerm) {
        searchResults.style.display = 'none';
        return;
    }

    const matches = Object.entries(predefinedProducts)
        .filter(([product]) =>
            product.toLowerCase().includes(searchTerm)
        )
        .sort(([a], [b]) => {
            // Exact matches first, then by string length
            const aStartsWith = a.toLowerCase().startsWith(searchTerm);
            const bStartsWith = b.toLowerCase().startsWith(searchTerm);
            if (aStartsWith && !bStartsWith) return -1;
            if (!aStartsWith && bStartsWith) return 1;
            return a.length - b.length;
        })
        .slice(0, 10); // Limit to top 10 matches

    searchResults.innerHTML = '';

    if (matches.length === 0) {
        const div = document.createElement('div');
        div.textContent = 'Продукт не найден. Нажмите +, чтобы добавить новый.';
        div.className = 'no-results';
        searchResults.appendChild(div);
    } else {
        matches.forEach(([product, price]) => {
            const div = document.createElement('div');
            div.className = 'search-result-item';
            div.innerHTML = `
                <span class="product-name">${product}</span>
                <span class="product-price">${price}₽</span>
            `;
            div.addEventListener('click', () => {
                addToList(product, price);
                searchResults.style.display = 'none';
                productSearch.value = '';
            });
            searchResults.appendChild(div);
        });
    }

    searchResults.style.display = 'block';
}

// Add product to list
function handleAddProduct() {
    const productName = productSearch.value.trim();
    if (productName) {
        const price = predefinedProducts[productName] || 0;
        addToList(productName, price);
        productSearch.value = '';
        searchResults.style.display = 'none';
    }
}

function addToList(name, price) {
    const existingItem = shoppingList.find(item => item.name === name);
    if (existingItem) {
        existingItem.quantity++;
    } else {
        shoppingList.push({
            name,
            price,
            quantity: 1
        });
    }
    saveAndRenderList();
}

// Render shopping list
function renderList() {
    productList.innerHTML = '';
    let total = 0;

    shoppingList.forEach((item, index) => {
        const li = document.createElement('li');
        li.className = 'list-item';
        const itemTotal = item.price * item.quantity;
        total += itemTotal;

        li.innerHTML = `
            <div class="item-info">
                <span class="item-name">${item.name}</span>
                <span class="item-price">${item.price}₽ × ${item.quantity} = ${itemTotal}₽</span>
            </div>
            <div class="item-actions">
                <div class="quantity-controls">
                    <button class="quantity-btn" onclick="updateQuantity(${index}, -1)">-</button>
                    <span>${item.quantity}</span>
                    <button class="quantity-btn" onclick="updateQuantity(${index}, 1)">+</button>
                </div>
                <button class="delete-btn" onclick="removeItem(${index})">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        `;
        productList.appendChild(li);
    });

    totalPrice.textContent = total.toFixed(2);
}

// Update quantity
function updateQuantity(index, change) {
    shoppingList[index].quantity += change;
    if (shoppingList[index].quantity <= 0) {
        shoppingList.splice(index, 1);
    }
    saveAndRenderList();
}

// Remove item
function removeItem(index) {
    shoppingList.splice(index, 1);
    saveAndRenderList();
}

// Clear list
function clearList() {
    if (confirm('Вы уверены, что хотите очистить список?')) {
        shoppingList = [];
        saveAndRenderList();
    }
}

// Refresh prices from bdex.ru
function refreshPrices() {
    const refreshBtn = document.getElementById('refreshPrices');
    refreshBtn.disabled = true;
    refreshBtn.innerHTML = '<i class="fas fa-sync-alt fa-spin"></i> Обновление...';

    // Fetch new prices from our API
    fetch('/api/prices')
        .then(response => response.json())
        .then(newPrices => {
            // Update predefined products with new prices
            Object.assign(predefinedProducts, newPrices);

            // Update prices in shopping list
            shoppingList = shoppingList.map(item => ({
                ...item,
                price: predefinedProducts[item.name] || item.price
            }));

            saveAndRenderList();

            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Обновить цены';
        })
        .catch(error => {
            console.error('Error updating prices:', error);
            alert('Ошибка при обновлении цен. Пожалуйста, попробуйте позже.');

            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Обновить цены';
        });
}

// Save to localStorage and render
function saveAndRenderList() {
    localStorage.setItem('shoppingList', JSON.stringify(shoppingList));
    renderList();
}

// Initial render
renderList();