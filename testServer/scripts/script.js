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


    // Функция для запросов
    async function apiRequest(url, options = {}) {
      const token = sessionStorage.getItem('token');
      console.log(token);
      if (token) options.headers = { ...options.headers, 'Authorization': `Bearer ${token}` };
      const response = await fetch(url, options);
      return response;
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

                document.getElementById('userName').textContent = userData.name;
                document.getElementById('userEmail').textContent = userData.email;

                console.log('Данные пользователя загружены:', userData);
            } else {
                console.error('Ошибка при загрузке данных пользователя');
            }
        } catch (error) {
            console.error('Ошибка при загрузке данных пользователя:', error);
        }
    }

    if (window.location.pathname.includes('profilePage.html') ||
        document.querySelector('.user-info')) {
        loadUserData();
    }
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
      else{alert('Ошибка генерации');}
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
      else{alert('Ошибка генерации');}
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
      else{alert('Ошибка генерации');}
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
      else{alert('Ошибка генерации');}
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

    logOutButton.addEventListener('click', (e) => {
    e.preventDefault();
    sessionStorage.removeItem('token');
    window.location.replace('releasePage.HTML');
    });

    const saveButton = document.querySelector('.save');
    saveButton?.addEventListener('click', async (e) => {
        e.preventDefault();

        const token = sessionStorage.getItem('token');

        if (!token) {
            alert('Токен не найден. Пожалуйста, войдите снова.');
            window.location.replace('releasePage.HTML');
            return;
        }

        const profileData = {
            about: document.getElementById('about')?.value || '',
            style: document.querySelectorAll('.user-style input[type="text"]')[0]?.value || '',
            color: document.querySelectorAll('.user-style input[type="text"]')[1]?.value || '',
            material: document.querySelectorAll('.user-style input[type="text"]')[2]?.value || '',
            height: document.querySelectorAll('.user-params input[type="text"]')[0]?.value || '',
            size: document.querySelectorAll('.user-params input[type="text"]')[1]?.value || '',
            gender: document.querySelectorAll('.user-params input[type="text"]')[2]?.value || ''
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


});

