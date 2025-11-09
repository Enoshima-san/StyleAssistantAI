document.addEventListener('DOMContentLoaded', function(){
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
    const generateButton = document.getElementById('generateButton');
    const tabButtons = document.getElementById('.tab-button');

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
        }).then(resp => { return resp.json() })
        .then(resp => { 
            console.log(resp);
            if (resp === "yea") 
            {
                alert('Регистрация завершена');
            }
            else{
                alert('Ошибка регистрации');
            }
        })
        .catch(err => { console.log(err) });
    })

    // отправка на сервер данных со страницы входа 
    loginForm?.addEventListener('submit', function(e) {
        e.preventDefault();
        let usermail = (document.getElementById("email").value);
        let password = (document.getElementById("password").value);
        const newPost = 
        {
            usermail,password
        }
        fetch('http://localhost:3000/login', 
        {
         method: 'POST',
         headers: {
            'Content-Type': 'application/json;charset=utf-8'
          },
         body: JSON.stringify(newPost)
        }).then(resp => { return resp.json() })
        .then(resp => { 
            console.log(resp);
            if (resp === "yea") 
            {
                alert('Авторизация завершена');
            }
            else{
                alert('Ошибка авторизации');
            }

        })
        .catch(err => { console.log(err) });
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

    generateButton?.addEventListener('click', function(e) {
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
        const newPost = 
        {
            gender,size,height,style,color,material,season,purpose,weather,climate
        }
        console.log(newPost)
        fetch('http://localhost:3000/prompt', 
        {
         method: 'POST',
         headers: {
            'Content-Type': 'application/json;charset=utf-8'
          },
         body: JSON.stringify(newPost)
        }).then(resp => { return resp.json() })
        .then(resp => { 
            console.log(resp);

            if (typeof resp === 'object' && resp.status === "yea")
            {
                alert('Генерация завершена');
                const keys = Object.keys(resp.dbResults);
                if (keys != null)
                {   
                    for (const key of keys) {
                        addProduct(resp.dbResults[key])
                    }
                }
                console.log('Результаты из БД:', resp.dbResults);
            }

            else if (resp === "yea")
            {
                alert('Генерация завершена');
            }
            else{
                alert('Ошибка генерации');
            }
            generateButton.disabled = false;

        })
        .catch(err => { console.log(err) });
    })
    
    tabButtons?.forEach(button => {
    button.addEventListener('click', () => {
        tabButtons.forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');
    });
});
});
