document.addEventListener('DOMContentLoaded', function(){
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');
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

    tabButtons?.forEach(button => {
    button.addEventListener('click', () => {
        tabButtons.forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');
    });
});
});
