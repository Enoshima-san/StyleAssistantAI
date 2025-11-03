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
    const message = req.body;
    const testPromt = `Опиши в 20 словах аутфит по следующим характеристикам: Пол-`+
    `${message.gender}, Размер-${message.size}, Рост-${message.height}, Стиль-${message.style},`+ 
    `Цвет-${message.color}, Материал-${message.material}, Сезон-${message.season}, Цель-${message.purpose},`+ 
    `Погода-${message.weather}, Климат-${message.climate}`;
    console.log(testPromt)
    const HUGGING_FACE_TOKEN = process.env.API_KEY;
    const client = new InferenceClient(HUGGING_FACE_TOKEN)
    try {
        const out = await client.chatCompletion({
            model: 'deepseek-ai/DeepSeek-R1',
            messages: [{ role: 'user', content: testPromt }],
            max_tokens: 512,
        })
        const originalString = out.choices[0].message.content
        let newString = originalString.replace(/<think>.*?<\/think>/gs, '')
        console.log(newString)

        // Ключевые слова
        const mainKeywords = [
            'рубашка', 'свитер', 'футболка', 'штаны', 'платье', 'юбка', 'брюки',
            'джинсы', 'куртка', 'пальто', 'кофта', 'топ', 'шорты', 'пиджак',
            'ветровка', 'толстовка', 'худи', 'майка', 'кеды', 'туфли',
            'костюм', 'плащ', 'пуховик', 'бомбер', 'кроссовки', 'лонгслив'
        ];

        const foundKeywords = [];
        for (const keyword of mainKeywords) {
            if (newString.toLowerCase().includes(keyword)) {
                foundKeywords.push(keyword);
            }
        }

        console.log('Найденные ключевые слова в ответе ИИ:', foundKeywords);

        let dbResults = [];

        if (foundKeywords.length > 0) {
            const placeholders = foundKeywords.map(() => '?').join(',');
            const sqlQuery = `
                SELECT
                    т.ID_Товара,
                    т.Название AS Название_Товара,
                    т.Описание,
                    т.Ссылка_Товар,
                    х.Бренд,
                    х.Состав,
                    х.Цвет,
                    х.Гендер,
                    х.Размер_на_Модели,
                    х.Рост_Модели,
                    х.Параметры_Модели,
                    х.Покрой,
                    х.Цена,
                    х.Ссылка_Изображение,
                    к.Название AS Категория,
                    б.Название AS Название_Бренда
                FROM Товары т
                LEFT JOIN Характеристики_Товаров х ON т.ID_Товара = х.ID_Товара
                LEFT JOIN Категории к ON т.ID_Категории = к.ID_Категории
                LEFT JOIN Бренды б ON т.ID_Бренда = б.ID_Бренда
                WHERE (к.Название IN (${placeholders}) 
                   OR т.Название LIKE '%${foundKeywords[0]}%' 
                   OR т.Описание LIKE '%${foundKeywords[0]}%')
                   AND х.Активен = 1
                LIMIT 10
            `;

            db.all(sqlQuery, foundKeywords, (err, rows) => {
                if (err) {
                    console.error('Ошибка при запросе к БД:', err.message);
                    res.send(JSON.stringify({
                        status: 'yea',
                        aiResponse: newString,
                        dbResults: [],
                        error: 'Ошибка базы данных'
                    }));
                } else {
                    console.log('Результаты из БД:');
                    console.log(`Найдено товаров: ${rows.length}`);

                    // Успешный ответ с данными из БД
                    res.send(JSON.stringify({
                        status: 'yea',
                        aiResponse: newString,
                        dbResults: rows,
                        keywords: foundKeywords
                    }));
                }
            });
        } else {
            console.log('Не найдено ключевых слов для поиска в БД');
            // Отправляем ответ без результатов БД
            res.send(JSON.stringify({
                status: 'yea',
                aiResponse: newString,
                dbResults: [],
                keywords: []
            }));
        }
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
