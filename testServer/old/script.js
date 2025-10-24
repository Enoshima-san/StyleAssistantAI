document.addEventListener('DOMContentLoaded', function() {
    // Поиск элементов страницы
    const regButton = document.getElementById('regButton') 
    const loginButton = document.getElementById('loginButton')

       // отправка на сервер данных со страницы регистрации 
       regButton?.addEventListener('click', function(e) {
        e.preventDefault();
        let username = (document.getElementById("usernameReg").value)
        let password = (document.getElementById("passwordReg").value)
            const newPost = 
        {
            username,password
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
    loginButton?.addEventListener('click', function(e) {
        e.preventDefault();
        let username = (document.getElementById("usernameLog").value);
        let password = (document.getElementById("passwordLog").value);
        const newPost = 
        {
            username,password
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
})