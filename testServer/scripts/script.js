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

    generateButton?.addEventListener('click', function(e) {
        e.preventDefault();
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
                console.log('Результаты из БД:', resp.dbResults);
            }

            else if (resp === "yea")
            {
                alert('Генерация завершена');
            }
            else{
                alert('Ошибка генерации');
            }

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
