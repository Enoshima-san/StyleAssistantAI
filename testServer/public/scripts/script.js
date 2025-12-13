document.addEventListener('DOMContentLoaded', function(){
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const generateButton = document.getElementById('generateButton');
    const tabButtons = document.getElementById('.tab-button');
    const profilePage = document.getElementById('userProfile');
    const favoritePage = document.getElementById('favorite');
    const catalogPage = document.getElementById('catalog');
    const generatePage = document.getElementById('recomendation');
    const heartButtons = document.querySelectorAll('.heart-icon');
    const likeDislikeButtons = document.querySelectorAll('.action-button');
    const logOutButton = document.getElementById('log-out');
    const saveButton = document.querySelector('.save');
    const saveOutfitButton = document.getElementById('saveButton');


    // Функция для запросов
    async function apiRequest(url, options = {}) {
      const token = sessionStorage.getItem('token');
      console.log(token);
      if (token) options.headers = { ...options.headers, 'Authorization': `Bearer ${token}` };
      const response = await fetch(url, options);
      return response;
    }
    function removeAllChildren(parentElement) {
        while (parentElement.firstChild) {
            parentElement.removeChild(parentElement.firstChild);
        }
    }
    registerForm?.addEventListener('submit', function(e) {
        e.preventDefault();
        let username = (document.getElementById("name").value)   
        let usermail = (document.getElementById("email").value)
        let password = (document.getElementById("password").value)
            const newPost = 
        {
            username,usermail,password
        }
        console.log(newPost)
        fetch('http://localhost:3000/registration', 
        {
         method: 'POST',
         headers: {
            'Content-Type': 'application/json;charset=utf-8'
          },
         body: JSON.stringify(newPost)
        }).then(resp => { 
            if (resp.ok) 
            {
                alert('Регистрация завершена');
                window.location.replace('releasePage.HTML');
            }
            else{
                alert('Ошибка регистрации');
            }
        })
        .catch(err => { console.log(err) });
    })

    // отправка на сервер данных со страницы входа 
    loginForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        let usermail = (document.getElementById("email").value);
        let password = (document.getElementById("password").value);
        try {
            const response = await fetch('http://localhost:3000/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json;charset=utf-8' },
                body: JSON.stringify({ usermail, password })
        });
        
        const data = await response.json();
        if (response.ok) 
            {
                sessionStorage.setItem('token', data.token);
                alert('Авторизация завершена');
                window.location.replace('releasePageGen.HTML');
            }
        else{
                alert('Ошибка авторизации');
            }

        } catch(error) {console.log(error)}
    })

    function addProduct(content) {
        const display = document.getElementById('products-display');
        const productDiv = document.createElement('div');
        const productImg = document.createElement('img');
        const productInfo = document.createElement('div');
        const productButton = document.createElement('a');
        const productInfoP1 = document.createElement('p');
        const productInfoP2 = document.createElement('p');
        const productInfoP3 = document.createElement('p');
        const productInfoP4 = document.createElement('p');
        productDiv.className = `product-card`;
         
        productImg.src = `${content.Ссылка_Изображение}`;
        productImg.width = "200";
        productImg.height = "200";
        productDiv.dataset.productId = content.ID_Товара;
        productInfo.className = 'product-info';
        productInfoP1.textContent = `Название: ${content.Название_Товара}`
        productInfoP2.textContent = `Цвет: ${content.Цвет}`
        productInfoP3.textContent = `Состав: ${content.Состав}`
        productInfoP4.textContent = `Цена: ${content.Цена} рублей`
        productButton.href = `${content.Ссылка_Товар}`;
        productButton.class = "product-button";
        productButton.textContent = "Купить"
        productInfo.appendChild(productInfoP1)
        productInfo.appendChild(productInfoP2)
        productInfo.appendChild(productInfoP3)
        productInfo.appendChild(productInfoP4)
        productInfo.appendChild(productButton)
        productDiv.appendChild(productImg);
        productDiv.appendChild(productInfo);
        display.appendChild(productDiv)
    }
        // Добавление карточки товара на странице каталога
      function addProductCatalog(content) {
        const display = document.getElementById('outfits-display');
        const productDiv = document.createElement('div');
        const productInfoHeader = document.createElement('div');
        const productInfoGrid = document.createElement('div');
        const productInfo = document.createElement('div');
        const productButtons = document.createElement('div');
        const productButtonHeart = document.createElement('div');
        const productImg = document.createElement('img');
        const productBuy = document.createElement('a');
        const productButtonLike = document.createElement('button');
        const productButtonDislike = document.createElement('button');
        const productInfoP2 = document.createElement('p');
        const productInfoP3 = document.createElement('p');
        const productInfoP4 = document.createElement('p');
        const productInfoTitle = document.createElement('h3');
    

        productDiv.className = `outfit-card`;
        productInfoHeader.className = `outfit-header`;
        productInfoGrid.className = `outfit-grid-added`;
        productButtons.className = `outfit-actions`;

        productInfoTitle.className = `outfit-title`;
        productButtonHeart.className = `heart-icon`;

        productInfoTitle.innerHTML  = `Название: ${content.Название_Товара}`;
        productButtonHeart.innerHTML  = `♥`;

        productInfo.className = 'outfit-item-added';
        productBuy.className = "outfit-button-added";
        productInfoP2.textContent = `Цвет: ${content.Цвет}`
        productInfoP3.textContent = `Состав: ${content.Состав}`
        productInfoP4.textContent = `Цена: ${content.Цена} рублей`
        productImg.src = `${content.Ссылка_Изображение}`;
        productImg.width = "200";
        productImg.height = "200";
        productBuy.href = `${content.Ссылка_Товар}`;
        productBuy.textContent = "Купить"

        productButtonLike.className = `action-button like-button`;
        productButtonDislike.className = `action-button dislike-button`;

        productButtonLike.innerHTML  = "👍 Лайк";
        productButtonDislike.innerHTML  = "👎 Дизлайк";

        productInfoHeader.appendChild(productInfoTitle);
        productInfoHeader.appendChild(productButtonHeart);
        productInfo.appendChild(productImg);
        productInfo.appendChild(productInfoP2);
        productInfo.appendChild(productInfoP3);
        productInfo.appendChild(productInfoP4);
        productInfo.appendChild(productBuy);
        productInfo.appendChild(productBuy);
        productInfoGrid.appendChild(productInfo);
        productButtons.appendChild(productButtonLike);
        productButtons.appendChild(productButtonDislike);
        productDiv.appendChild(productInfoHeader);
        productDiv.appendChild(productInfoGrid);
        productDiv.appendChild(productButtons);
        display.appendChild(productDiv)

    }

    function removeAllChildren(parentElement) {
      while (parentElement.firstChild) {
        parentElement.removeChild(parentElement.firstChild);
      }
    }
    async function loadUserData() {
        try {
            const response = await apiRequest('http://localhost:3000/user-data');
            if (response.ok) {
                const userData = await response.json();
                
                if(document.querySelector('.user-info')) {
                    document.getElementById('userName').textContent = userData.name;
                    document.getElementById('userEmail').textContent = userData.email;
                }
                document.getElementById('style').value = userData.style || "";
                document.getElementById('color').value = userData.color || "";
                document.getElementById('material').value = userData.material || "";

                document.getElementById('height').value = userData.height || "";
                document.getElementById('size').value = userData.size || "";
                document.getElementById('gender').value = userData.gender || "";

                console.log('Данные пользователя загружены:', userData);
            } else {
                console.error('Ошибка при загрузке данных пользователя');
            }
        } catch (error) {
            console.error('Ошибка при загрузке данных пользователя:', error);
        }
    }

    async function loadUserOutfits() {
        try {
            const token = sessionStorage.getItem('token');

            if (!token) {
                window.location.replace('releasePage.HTML');
                return;
            }

            const response = await fetch('http://localhost:3000/user-outfits', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (response.ok) {
                const outfits = await response.json();

                const container = document.querySelector('.outfits') ||
                    document.getElementById('outfits-display');

                if (!container) {
                    console.error('Контейнер для образов не найден');
                    return;
                }
                removeAllChildren(container);

                if (!outfits || outfits.length === 0) {
                    container.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #666;">
                    <p>У вас пока нет сохраненных образов</p>
                    <p>Сгенерируйте образ на вкладке "Рекомендация" и нажмите "Сохранить аутфит"</p>
                </div>`;
                    return;
                }

                outfits.forEach(outfit => {
                    createFavoriteOutfitCard(outfit);
                });
            } else {
                const container = document.querySelector('.outfits');
                if (container) {
                    container.innerHTML = '<p style="text-align: center; padding: 40px; color: #666;">Ошибка загрузки избранного. Попробуйте обновить страницу.</p>';
                }
            }
        } catch (error) {
            const container = document.querySelector('.outfits');
            if (container) {
                container.innerHTML = '<p style="text-align: center; padding: 40px; color: #666;">Ошибка сети при загрузке избранного.</p>';
            }
        }
    }

// Функция удаления образа
    async function deleteOutfit(outfitId, outfitCardElement) {
        if (!confirm('Вы уверены, что хотите удалить этот образ?')) {
            return;
        }
        try {
            const response = await apiRequest(`http://localhost:3000/delete-outfit/${outfitId}`, {
                method: 'DELETE'
            });
            if (response.ok) {
                outfitCardElement.remove();
                alert('Образ удален');
            } else {
                alert('Ошибка при удалении образа');
            }
        } catch (error) {
            console.error('Ошибка при удалении образа:', error);
            alert('Ошибка сети при удалении образа');
        }
    }

    function createFavoriteOutfitCard(outfit) {
        const container = document.querySelector('.outfits') || document.getElementById('outfits-display');
        if (!container) return;

        const outfitCard = document.createElement('div');
        outfitCard.className = 'outfit-card';
        outfitCard.dataset.outfitId = outfit.outfitId;

        const outfitHeader = document.createElement('div');
        outfitHeader.className = 'outfit-header';

        const outfitTitle = document.createElement('h3');
        outfitTitle.className = 'outfit-title';
        outfitTitle.textContent = outfit.outfitName || 'Сохраненный образ';

        const deleteButton = document.createElement('div');
        deleteButton.className = 'heart-icon';
        deleteButton.innerHTML = '♥';
        deleteButton.style.cursor = 'pointer';
        deleteButton.style.color = '#ff4757';
        deleteButton.style.fontSize = '20px';
        deleteButton.title = 'Удалить образ';
        deleteButton.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteOutfit(outfit.outfitId, outfitCard);
        });

        outfitHeader.appendChild(outfitTitle);
        outfitHeader.appendChild(deleteButton);

        const outfitGrid = document.createElement('div');
        outfitGrid.className = 'outfit-grid';

        // Если есть товары
        if (outfit.products && outfit.products.length > 0) {

            // Берем максимум 4 товара
            const maxProducts = Math.min(outfit.products.length, 4);
            let hasValidProducts = false;

            for (let i = 0; i < maxProducts; i++) {
                const product = outfit.products[i];
                const productItem = document.createElement('div');
                productItem.className = 'outfit-item';

                // Картинка товара
                if (product.productImage && product.productImage !== '') {
                    const productImage = document.createElement('img');
                    productImage.src = product.productImage;
                    productImage.alt = product.productName || 'Товар';
                    productImage.style.width = '100%';
                    productImage.style.height = '100%';
                    productImage.style.objectFit = 'cover';
                    productImage.style.borderRadius = '4px';
                    productItem.appendChild(productImage);
                    hasValidProducts = true;
                } else {
                    productItem.innerHTML = '<span style="color: #999; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);">Нет изображения</span>';
                    hasValidProducts = true;
                }

                // Кнопка "Купить"
                if (product.productLink && product.productLink !== '') {
                    const buyButton = document.createElement('a');
                    buyButton.href = product.productLink;
                    buyButton.target = '_blank';
                    buyButton.className = 'buy-button';
                    buyButton.textContent = 'Купить';
                    buyButton.style.position = 'absolute';
                    buyButton.style.bottom = '5px';
                    buyButton.style.left = '50%';
                    buyButton.style.transform = 'translateX(-50%)';
                    buyButton.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
                    buyButton.style.color = 'white';
                    buyButton.style.padding = '5px 10px';
                    buyButton.style.borderRadius = '5px';
                    buyButton.style.textDecoration = 'none';
                    buyButton.style.fontSize = '12px';
                    buyButton.style.zIndex = '10';

                    productItem.appendChild(buyButton);
                }

                outfitGrid.appendChild(productItem);
            }

            if (!hasValidProducts) {
                const emptyMessage = document.createElement('div');
                emptyMessage.style.gridColumn = '1 / span 2';
                emptyMessage.style.gridRow = '1 / span 2';
                emptyMessage.style.display = 'flex';
                emptyMessage.style.alignItems = 'center';
                emptyMessage.style.justifyContent = 'center';
                emptyMessage.style.color = '#666';
                emptyMessage.style.fontSize = '14px';
                emptyMessage.style.textAlign = 'center';
                emptyMessage.textContent = 'В этом образе нет товаров с изображениями';
                outfitGrid.innerHTML = ''; // Очищаем сетку
                outfitGrid.appendChild(emptyMessage);
            } else {
                const emptySlots = 4 - maxProducts;
                for (let i = 0; i < emptySlots; i++) {
                    const emptyItem = document.createElement('div');
                    emptyItem.className = 'outfit-item';
                    emptyItem.innerHTML = '<span style="color: #999; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);">Нет товара</span>';
                    outfitGrid.appendChild(emptyItem);
                }
            }
        } else {
            console.log('У образа нет товаров');
            const emptyMessage = document.createElement('div');
            emptyMessage.style.gridColumn = '1 / span 2';
            emptyMessage.style.gridRow = '1 / span 2';
            emptyMessage.style.display = 'flex';
            emptyMessage.style.alignItems = 'center';
            emptyMessage.style.justifyContent = 'center';
            emptyMessage.style.color = '#666';
            emptyMessage.style.fontSize = '14px';
            emptyMessage.style.textAlign = 'center';
            emptyMessage.textContent = 'В этом образе пока нет товаров';
            outfitGrid.appendChild(emptyMessage);
        }

        outfitCard.appendChild(outfitHeader);
        outfitCard.appendChild(outfitGrid);
        container.appendChild(outfitCard);
    }

    // Загрузка товаров на странице каталога
      async function loadUserDataCatalog() {
        try {
            const response = await apiRequest('http://localhost:3000/user-data');
            if (response.ok) {
                const userData = await response.json();
                let gender = userData.gender || 'Женский';
                let size = userData.size || '45';
                let height = userData.height  ||'165';
                let style = userData.style || 'Повседневный';
                let color = userData.color || "Любой";
                let material = userData.material || "Любой";
                let season = "Любой";
                let purpose = "Любой";
                let weather = "Любая";
                let climate = "Любой";
                const resp = await fetch('http://localhost:3000/prompt', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json;charset=utf-8'
                    },
                    body: JSON.stringify({gender,size,height,style,color,material,season,purpose,weather,climate})
                });
                const data = await resp.json();
                if (resp.ok) 
                {
                    alert('Генерация завершена');
                    const keys = Object.keys(data.dbResults);
                    sessionStorage.setItem('aiAnswer', data.aiResponse);
                    sessionStorage.setItem('aiPrompt', data.aiPrompt);
                    saveOutfitButton.disabled = false;
                    if (keys != null)
                    {   
                        for (const key of keys) {
                            addProductCatalog(data.dbResults[key])
                        }
                    }
                    console.log('Результаты из БД:', data.dbResults);
                }
                else{
                    alert('Ошибка генерации');
                }
                console.log('Данные пользователя загружены:', userData);
            } else {
                console.error('Ошибка при загрузке данных пользователя');
            }
        } catch (error) {
            console.error('Ошибка при загрузке данных пользователя:', error);
        }
    }

    if (window.location.pathname.includes('profilePage.html') ||
        document.querySelector('.user-info') || window.location.pathname.includes('releasePageGen.html') || document.querySelector('.form-section')) {
        loadUserData();
    }
    // Выполнение функций при заходе на страницу каталога
    if (window.location.pathname.includes('catalogPage.html') ||
        document.querySelector('.outfits')) {
        const container = document.querySelector('.outfits');
        removeAllChildren(container);
        loadUserDataCatalog();
    }
    // Кнопка создания образа с запросом на сервер по параметрам
    generateButton?.addEventListener('click', async(e) => {
        e.preventDefault();
        const container = document.getElementById('products-display');
        generateButton.disabled = true
        removeAllChildren(container);
        let gender = (document.getElementById("gender")?.value);
        let size = (document.getElementById("size")?.value);
        let height = (document.getElementById("height")?.value);
        let style = (document.getElementById("style")?.value);
        if (gender === '' || size === '' || height === '' || style === '') {
            alert('Заполните все обязательные поля')
            return;
        }        
        let color = (document.getElementById("color")?.value) || "Любой";
        let material = (document.getElementById("material")?.value) || "Любой";
        let season = (document.getElementById("season")?.value) || "Любой";
        let purpose = (document.getElementById("purpose")?.value) || "Любой";
        let weather = (document.getElementById("weather")?.value) || "Любая";
        let climate = (document.getElementById("climate")?.value) || "Любой";
        try {
            const resp = await apiRequest('http://localhost:3000/protected');
            if (resp.ok)
            {
                const response = await fetch('http://localhost:3000/prompt', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json;charset=utf-8'
                    },
                    body: JSON.stringify({gender,size,height,style,color,material,season,purpose,weather,climate})
                });
                const data = await response.json();
                if (response.ok) 
                {
                    alert('Генерация завершена');
                    saveOutfitButton.disabled = false;
                    sessionStorage.setItem('aiAnswer', data.aiResponse);
                    sessionStorage.setItem('aiPrompt', data.aiPrompt);
                    const keys = Object.keys(data.dbResults);
                    
                    if (keys != null)
                    {   
                        for (const key of keys) {
                            addProduct(data.dbResults[key])
                        }
                    }
                    console.log('Результаты из БД:', data.dbResults);
                }
                else{
                    alert('Ошибка генерации');
                }
                generateButton.disabled = false;
            }
            else{
                alert('Ошибка доступа')
                generateButton.disabled = false;
            }
        } catch(error) {console.log(error)}
    })
    // Кнопка сохранения образа на сервер
    saveOutfitButton?.addEventListener('click', async(e) => {
        e.preventDefault();
        const token = sessionStorage.getItem('token');
        if (!token) {
            alert('Токен не найден. Пожалуйста, войдите снова.');
            window.location.replace('releasePage.HTML');
            return;
        }

        const productCards = document.querySelectorAll('.product-card');
        const productIds = Array.from(productCards).map(card => {
            return card.dataset.productId;
        }).filter(id => id && id !== 'undefined');

        try {
            let aiResponse = sessionStorage.getItem('aiAnswer');
            let aiPrompt = sessionStorage.getItem('aiPrompt');

            const response = await apiRequest('http://localhost:3000/saveAnswer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    aiResponse,
                    aiPrompt,
                    productIds: productIds
                })
            });

            if (response.ok) {
                alert('Образ успешно сохранен!');
            } else {
                const errorText = await response.text();
                alert('Ошибка при сохранении образа: ' + response.status);
            }
        } catch(error) {
            alert('Ошибка сети при сохранении образа');
        }
    });

    // Доступ к странице профиля
    profilePage?.addEventListener('click', async (e) => {
    e.preventDefault();
    try {
      const data = await apiRequest('http://localhost:3000/protected');
      console.log(data.message);
      if (data.ok)
      {
        window.location.replace('profilePage.HTML');
      }
      else{alert('Ошибка доступа');}
    } catch (error) {
      console.log(error);
      sessionStorage.removeItem('token');
    }
    });

    catalogPage?.addEventListener('click', async (e) => {
    e.preventDefault();
    try {
      const data = await apiRequest('http://localhost:3000/protected');
      console.log(data.message);
      if (data.ok)
      {
        window.location.replace('catalogPage.HTML');
      }
      else{alert('Ошибка доступа');}
    } catch (error) {
      console.log(error);
      sessionStorage.removeItem('token');
    }
    });

    favoritePage?.addEventListener('click', async (e) => {
    e.preventDefault();
    try {
      const data = await apiRequest('http://localhost:3000/protected');
      console.log(data.message);
      if (data.ok)
      {
        window.location.replace('favoritePage.HTML');
      }
      else{alert('Ошибка доступа');}
    } catch (error) {
      console.log(error);
      sessionStorage.removeItem('token');
    }
    });

    generatePage?.addEventListener('click', async (e) => {
    e.preventDefault();
    try {
      const data = await apiRequest('http://localhost:3000/protected');
      console.log(data.message);
      if (data.ok)
      {
        window.location.replace('releasePageGen.HTML');
      }
      else{alert('Ошибка доступа');}
    } catch (error) {
      console.log(error);
      sessionStorage.removeItem('token');
    }
    });

    tabButtons?.forEach(button => {
    button.addEventListener('click', () => {
        tabButtons.forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');
    });
    });

    heartButtons?.forEach(button => {
        button.addEventListener('click', () => {
            button.classList.toggle('active');
        });
    });

    likeDislikeButtons?.forEach(button => {
        button.addEventListener('click', function() {
            const card = this.closest('.outfit-card');
            setTimeout(() => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                setTimeout(() => {
                    card.remove();
                    if (document.querySelectorAll('.outfit-card').length === 0) {
                        const outfitsContainer = document.querySelector('.outfits');
                        outfitsContainer.innerHTML = '<p style="text-align: center; padding: 40px; color: #666;">Нет образов для оценки</p>';
                    }
                }, 300);
            }, 300);
        });
    });

    logOutButton?.addEventListener('click', (e) => {
    e.preventDefault();
    sessionStorage.removeItem('token');
    window.location.replace('releasePage.HTML');
    });

    saveButton?.addEventListener('click', async (e) => {
        e.preventDefault();

        const token = sessionStorage.getItem('token');

        if (!token) {
            alert('Токен не найден. Пожалуйста, войдите снова.');
            window.location.replace('releasePage.HTML');
            return;
        }

        const profileData = {
            about: document.getElementById('about')?.value || 'Пользователь',
            style: document.querySelectorAll('.user-style input[type="text"]')[0]?.value || 'Любой',
            color: document.querySelectorAll('.user-style input[type="text"]')[1]?.value || 'Любой',
            material: document.querySelectorAll('.user-style input[type="text"]')[2]?.value || 'Любой',
            height: document.querySelectorAll('.user-params input[type="text"]')[0]?.value || 'Любой',
            size: document.querySelectorAll('.user-params input[type="text"]')[1]?.value || 'Любой',
            gender: document.querySelectorAll('.user-params input[type="text"]')[2]?.value || 'Любой'
        };

        try {
            const response = await apiRequest('http://localhost:3000/save-profile', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(profileData)
            });

            if (response.ok) {
                const result = await response.json();
                alert('Профиль успешно сохранен!');
                console.log('Профиль сохранен:', result);
            } else {
                console.log('Статус ответа:', response.status);
                const errorText = await response.text();
                console.log('Текст ошибки:', errorText);
                alert('Ошибка при сохранении профиля: ' + response.status);
            }
        } catch (error) {
            console.error('Ошибка сети:', error);
            alert('Ошибка сети при сохранении профиля');
        }
    });
    // Для страницы избранного
    if (window.location.pathname.includes('favoritePage.html') ||
        document.getElementById('favorite')?.classList.contains('active')) {
        setTimeout(() => {
            const container = document.querySelector('.outfits') || document.getElementById('outfits-display');
            if (container) {
                removeAllChildren(container);
                container.innerHTML = '<p style="text-align: center; padding: 20px;">Загрузка избранного...</p>';
                loadUserOutfits();
            } else {
                // Создаем контейнер если его нет
                const mainContainer = document.querySelector('.container');
                if (mainContainer) {
                    const newContainer = document.createElement('div');
                    newContainer.className = 'outfits';
                    newContainer.id = 'outfits-display';
                    mainContainer.appendChild(newContainer);
                    loadUserOutfits();
                }
            }
        }, 100);
    }


});

