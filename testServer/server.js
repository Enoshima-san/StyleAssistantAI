// Подключние фреймворков и библиотек
const express = require('express');
const cors = require('cors');
const sqlite3 = require('sqlite3').verbose()

// Подключение базы данных
const db = new sqlite3.Database("testDatabase.db" ,sqlite3.OPEN_READWRITE, (err) => {
    if(err)
    {
        console.log("Error Occurred - " + err.message);
    }
    else
    {
        console.log("DataBase Connected");
    }
});

// Иницилизация фреймворка Express
const app = express();
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }))


// Получение данных на сервер и вставка их в базу данных
app.post('/registration', (request, response) => {
    const data = request.body
    let flag = "bad";
    db.serialize(() => {
        db.get('SELECT indexTest as id FROM mainTest ORDER BY id DESC LIMIT 1;', (err, row) => {
        if (err) {
            console.error(err.message);
            response.status(400);
            response.send(JSON.stringify(flag));
            response.end();
        } else {
            let userID
            if (row == undefined) userID = 0
            else userID = row.id + 1
            let stmt = db.prepare('INSERT INTO mainTest VALUES (?,?,?)')
            stmt.run(`${userID}`,`${data.username}`,`${data.password}`,(err) =>{
                if (err)
                {
                    console.error(err.message);
                    stmt.finalize()
                    response.status(400);
                    response.send(JSON.stringify(flag));
                    response.end();
                }
                else{ flag = "yea";
                    stmt.finalize()
                    response.status(201);
                    response.send(JSON.stringify(flag));
                    response.end();
                }            
            });
        }
    })
    })
});

// Получение данных на сервер и сверка их с существующими в базе данных
app.post('/login', (request, response) => {
    const data = request.body
    let flag = "bad";
    db.serialize(() => {
        db.get(`SELECT textTest as name, numTest as pass FROM mainTest WHERE name='${data.username}' AND pass='${data.password}';`, (err, row) => {
        if (err) {
            console.error(err.message);
            response.status(400);
            response.send(JSON.stringify(flag));
            response.end();
       } else {
            if (row != undefined && row.name === data.username && row.pass === data.password)
            {
                console.log("ye")
                flag = "yea";
             }
            response.status(201);
            response.send(JSON.stringify(flag));
            response.end();
       }
        })
    })
});

// Иницилизация сервера по порту 3000
app.listen(3000, () => {
    console.log('Server running on port 3000');
});