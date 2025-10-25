// Подключние фреймворков и библиотек
import { InferenceClient  } from "@huggingface/inference";
import express from 'express';
import cors from 'cors';
import sqlite3 from 'sqlite3'
import dotenv from 'dotenv'
import { randomUUID } from 'crypto';

dotenv.config({ path: './.env' });

// Подключение базы данных
const db = new sqlite3.Database("BD_test.db" ,sqlite3.OPEN_READWRITE, (err) => {
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

    // Проверяем, существует ли пользователь с такой почтой
    db.get('SELECT * FROM Пользователи WHERE Почта = ?', [data.usermail], (err, row) => {
        if (err) {
            console.error(err.message);
            response.status(400);
            response.send(JSON.stringify(flag));
            response.end();
            return;
        }

        if (row) {
            // Пользователь уже существует
            console.log("User already exists:", data.usermail);
            response.status(400);
            response.send(JSON.stringify(flag));
            response.end();
            return;
        }

        // Новый пользователь
        const userId = randomUUID();
        const currentDate = new Date().toISOString();

        db.run('INSERT INTO Пользователи (ID_Пользователя, Почта, Пароль, Имя, Дата_Регистрации) VALUES (?, ?, ?, ?, ?)',
            [userId, data.usermail, data.password, data.username, currentDate],
            (err) => {
                if (err) {
                    console.error(err.message);
                    response.status(400);
                    response.send(JSON.stringify(flag));
                    response.end();
                } else {
                    flag = "yea";
                    console.log("User registered successfully:", data.usermail);
                    response.status(201);
                    response.send(JSON.stringify(flag));
                    response.end();
                }
            }
        );
    });
});

// Получение данных на сервер и сверка их с существующими в базе данных
app.post('/login', (request, response) => {
    const data = request.body;
    let flag = "bad";

    db.get('SELECT ID_Пользователя, Имя FROM Пользователи WHERE Почта = ? AND Пароль = ?',
        [data.usermail, data.password],
        (err, row) => {
            if (err) {
                console.error(err.message);
                response.status(400);
                response.send(JSON.stringify(flag));
                response.end();
            } else {
                if (row) {
                    console.log("Login successful for user:", data.usermail);
                    flag = "yea";
                }
                response.status(201);
                response.send(JSON.stringify(flag));
                response.end();
            }
        }
    );
});

// Получение запроса на сервер и отправка промпта на сервер ИИ через Hugging Face
app.post('/prompt', async (req, res) => {
    const {message} = req.body;
    const modelId = 'deepseek-ai/DeepSeek-R1'
    const HUGGING_FACE_TOKEN = process.env.API_KEY; // Store securely
    const client = new InferenceClient(HUGGING_FACE_TOKEN)
    try {
        const out = await client.chatCompletion({
            model: 'deepseek-ai/DeepSeek-R1',
            messages: [{ role: 'user', content: message }],
            max_tokens: 512,
        });;
        res.json(out.choices[0].message);
    } catch (error) {
        console.error('Hugging Face API error:', error.response ? error.response.data : error.message);
        res.status(500).json({ error: 'Failed to perform inference' });
    }
});

// Иницилизация сервера по порту 3000
const PORT = process.env.PORT
app.listen(PORT, () => {
    console.log(`✅ Server running on port ${PORT}`);
});
