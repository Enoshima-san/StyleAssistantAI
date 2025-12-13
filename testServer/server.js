// Подключние фреймворков и библиотек
/*
import { InferenceClient  } from "@huggingface/inference";
import express from 'express';
import cors from 'cors';
import sqlite3 from 'sqlite3'
import dotenv from 'dotenv'
import { randomUUID } from 'crypto';
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import path from "path";
import { fileURLToPath } from "url"; */
const { InferenceClient } = require("@huggingface/inference");
const express = require("express");
const cors = require("cors");
const sqlite3 = require("sqlite3");
const dotenv = require("dotenv");
const { randomUUID } = require("crypto");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const path = require("path");

dotenv.config({ path: path.join(__dirname, ".env") });

const dbPath = path.join(process.cwd(), "db", "BD_test.db");

// Подключение базы данных
const db = new sqlite3.Database(dbPath ,sqlite3.OPEN_READWRITE, (err) => {
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
app.use(express.static(path.join(__dirname, "public")));

// Получение данных на сервер и вставка их в базу данных
app.post('/registration', async (request, response) => {
    const data = request.body
    // Проверяем, существует ли пользователь с такой почтой
    bcrypt.genSalt(10, (err, salt) => {
        if (err) {
            console.error(err);
            response.status(400);
            response.end();
        }
        bcrypt.hash(data.password, salt, (err, hash) => {
            if (err) {
                console.error(err);
                response.status(400);
                response.end();
            }
            db.get('SELECT * FROM Пользователи WHERE Почта = ?', [data.usermail], (err, row) => {
                if (err) {
                    console.error(err);
                    response.status(400);
                    response.end();
                    return;
                }
            
                if (row) {
                    // Пользователь уже существует
                    console.log("User already exists:", data.usermail);
                    response.status(400);
                    response.end();
                    return;
                }
            
                // Новый пользователь
                const userId = randomUUID();
                const currentDate = new Date().toISOString();
            
                db.run('INSERT INTO Пользователи (ID_Пользователя, Почта, Пароль, Имя, Дата_Регистрации) VALUES (?, ?, ?, ?, ?)',
                    [userId, data.usermail, hash, data.username, currentDate],
                    (err) => {
                        if (err) {
                            console.error(err);
                            response.status(400);
                            response.end();
                        } else {
                            console.log("User registered successfully:", data.usermail);
                            response.status(201);
                            response.end();
                        }
                    }
                );
            });
        });
    });
});

// Получение данных на сервер и сверка их с существующими в базе данных
app.post('/login', async (request, response) => {
    const data = request.body;
    db.get('SELECT ID_Пользователя as userId, Имя as userName, Пароль as hashedPassword FROM Пользователи WHERE Почта = ?',
        [data.usermail],
        (err, row) => {
            if (err) {
                console.error(err);
                response.status(400);
                response.end();
            } else {
                if (row) {
                    const storedHash = row.hashedPassword;
                    bcrypt.compare(data.password, storedHash, (err, result) => {
                        if (err) {
                            console.error(err);
                            response.status(400);
                            response.end();
                        }
                        if (result) {
                            console.log("Login successful for user:", data.usermail);
                            const token = jwt.sign({ userId: row.userId, username: row.userName }, process.env.SECRET_KEY, { expiresIn: '1h' });
                            response.json({ token, message: 'Вход успешен' });
                            response.status(201);
                            response.end();
                        } else {
                            console.error(err);
                            response.status(400);
                            response.end();
                        }
                    });
                }
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

            const userGender = message.gender.toLowerCase();
            let genderCondition = '';

            if (userGender.includes('муж') || userGender.includes('male') || userGender.includes('man')) {
                genderCondition = `
                    AND (
                        х.Гендер LIKE '%Мужской%' OR 
                        х.Гендер LIKE '%Мальчики%' OR 
                        х.Гендер LIKE '%male%' OR 
                        х.Гендер LIKE '%man%' OR
                        х.Гендер LIKE '%Мужской, Женский%' OR
                        х.Гендер LIKE '%Мальчики, Девочки%'
                    )
                `;
            }
            else if (userGender.includes('жен') || userGender.includes('female') || userGender.includes('woman')) {
                genderCondition = `
                    AND (
                        х.Гендер LIKE '%Женский%' OR 
                        х.Гендер LIKE '%Девочки%' OR 
                        х.Гендер LIKE '%female%' OR 
                        х.Гендер LIKE '%woman%' OR
                        х.Гендер LIKE '%Женский, Мужской%' OR
                        х.Гендер LIKE '%Девочки, Мальчики%' OR
                        х.Гендер IS NULL
                    )
                `;
            }

            const userColor = message.color ? message.color.toLowerCase() : 'любой';
            const userMaterial = message.material ? message.material.toLowerCase() : 'любой';

            let orderByConditions = [];

            if (userColor !== 'любой' && userMaterial !== 'любой') {
                orderByConditions.push(`
                    CASE 
                        WHEN (LOWER(х.Цвет) LIKE '%${userColor}%' AND LOWER(х.Состав) LIKE '%${userMaterial}%') THEN 1
                        WHEN (LOWER(х.Цвет) LIKE '%${userColor}%' OR LOWER(х.Состав) LIKE '%${userMaterial}%') THEN 2
                        ELSE 3
                    END
                `);
            } else if (userColor !== 'любой') {
                orderByConditions.push(`
                    CASE 
                        WHEN LOWER(х.Цвет) LIKE '%${userColor}%' THEN 1
                        ELSE 2
                    END
                `);
            } else if (userMaterial !== 'любой') {
                orderByConditions.push(`
                    CASE 
                        WHEN LOWER(х.Состав) LIKE '%${userMaterial}%' THEN 1
                        ELSE 2
                    END
                `);
            }
            orderByConditions.push('RANDOM()');

            const orderByClause = orderByConditions.length > 0 ?
                `ORDER BY ${orderByConditions.join(', ')}` :
                'ORDER BY RANDOM()';

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
                   ${genderCondition}
                   AND х.Активен = 1
                ${orderByClause}
                LIMIT 10
            `;

            db.all(sqlQuery, foundKeywords, (err, rows) => {
                if (err) {
                    console.error('Ошибка при запросе к БД:', err.message);
                    res.send(JSON.stringify({
                        status: 'yea',
                        aiResponse: newString,
                        dbResults: [],
                        error: 'Ошибка базы данных: ' + err.message
                    }));
                } else {
                    console.log('Результаты из БД:');
                    console.log(`Найдено товаров: ${rows.length}`);

                    if (rows.length > 0) {
                        const perfectMatch = rows.filter(row =>
                            (userColor === 'любой' || (row.Цвет && row.Цвет.toLowerCase().includes(userColor))) &&
                            (userMaterial === 'любой' || (row.Состав && row.Состав.toLowerCase().includes(userMaterial)))
                        );

                        const partialMatch = rows.filter(row =>
                            (userColor !== 'любой' && row.Цвет && row.Цвет.toLowerCase().includes(userColor)) ||
                            (userMaterial !== 'любой' && row.Состав && row.Состав.toLowerCase().includes(userMaterial))
                        );

                    }

                    // Успешный ответ с данными из БД
                    res.send(JSON.stringify({
                        status: 'yea',
                        aiResponse: newString,
                        dbResults: rows,
                        keywords: foundKeywords,
                        aiPrompt: testPromt
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

// Проверка токена на подлинность
const authenticateToken = (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];  // Bearer TOKEN
    if (!token) {
      return res.status(401).json({ error: 'Доступ запрещен' });
    }
    jwt.verify(token, process.env.SECRET_KEY, (err, user) => {
      if (err) return res.status(403).json({ error: 'Неверный токен' });
      req.user = user;
      next();
    });
};

// Сохранение образа в бд
app.post('/saveAnswer', authenticateToken, async (request, response) => {
    const userId = request.user.userId;
    const data = request.body;
    const currentDate = new Date().toISOString();
    const outfitId = randomUUID();

    try {
        // Сохраняем образ
        db.run('INSERT INTO Образы (ID_Образа, ID_Пользователя, Название, Параметры_Генерации, Дата_Создания) VALUES (?, ?, ?, ?, ?)',
            [outfitId, userId, data.aiResponse, data.aiPrompt, currentDate],
            (err) => {
                if (err) {
                    console.error('Ошибка сохранения образа:', err.message);
                    return response.status(400).json({
                        error: 'Ошибка сохранения образа',
                        details: err.message
                    });
                }

                console.log('Образ сохранен, ID:', outfitId);

                // Сохраняем товары образа (если есть)
                if (data.productIds && data.productIds.length > 0) {
                    console.log('Начинаю сохранение товаров...');

                    let completed = 0;
                    const total = data.productIds.length;

                    data.productIds.forEach((productId, index) => {
                        if (!productId || productId === 'undefined' || productId === 'null') {
                            completed++;
                            if (completed === total) {
                                response.status(201).json({
                                    message: 'Образ сохранен (некоторые товары пропущены)',
                                    outfitId: outfitId
                                });
                            }
                            return;
                        }

                        // Сохраняем элемент образа
                        db.run('INSERT INTO Элементы_Образа (ID_Образа, ID_Товара, Позиция) VALUES (?, ?, ?)',
                            [outfitId, productId, index + 1],
                            (err) => {
                                if (err) {
                                    console.error('Ошибка сохранения элемента:', err.message);
                                } else {
                                    console.log(`Сохранен товар ${index + 1}/${total}: ${productId}`);
                                }

                                completed++;
                                if (completed === total) {
                                    response.status(201).json({
                                        message: 'Образ и товары сохранены',
                                        outfitId: outfitId
                                    });
                                }
                            }
                        );
                    });
                } else {
                    console.log('Нет товаров для сохранения');
                    response.status(201).json({
                        message: 'Образ сохранен без товаров',
                        outfitId: outfitId
                    });
                }
            }
        );
    } catch (error) {
        console.error('Общая ошибка при сохранении:', error);
        response.status(500).json({
            error: 'Внутренняя ошибка сервера',
            details: error.message
        });
    }
});


app.post('/save-profile', authenticateToken, async (request, response) => {
    const userId = request.user.userId;
    const data = request.body;

    db.get('SELECT * FROM Профили_Пользователей WHERE ID_Пользователя = ?', [userId], (err, row) => {
        if (err) {
            console.error('Ошибка при проверке профиля:', err);
            response.status(500).json({ error: 'Ошибка базы данных' });
            return;
        }

        const currentDate = new Date().toISOString();

        if (row) {
            const sql = `UPDATE Профили_Пользователей 
                        SET О_Себе = ?, Стиль = ?, Цвет = ?, Материал = ?, 
                            Рост = ?, Размер_Одежды = ?, Пол = ?, Дата_Обновления = ?
                        WHERE ID_Пользователя = ?`;

            db.run(sql, [
                data.about, data.style, data.color, data.material,
                data.height, data.size, data.gender, currentDate, userId
            ], (err) => {
                if (err) {
                    console.error('Ошибка при обновлении профиля:', err);
                    response.status(500).json({ error: 'Ошибка обновления профиля' });
                } else {
                    console.log("Профиль обновлен для пользователя:", userId);
                    response.json({ message: 'Профиль успешно обновлен' });
                }
            });
        } else {
            const sql = `INSERT INTO Профили_Пользователей 
                        (ID_Пользователя, О_Себе, Стиль, Цвет, Материал, Рост, Размер_Одежды, Пол, Дата_Обновления)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`;

            db.run(sql, [
                userId, data.about, data.style, data.color, data.material,
                data.height, data.size, data.gender, currentDate
            ], (err) => {
                if (err) {
                    console.error('Ошибка при создании профиля:', err);
                    response.status(500).json({ error: 'Ошибка сохранения профиля' });
                } else {
                    console.log("Профиль создан для пользователя:", userId);
                    response.json({ message: 'Профиль успешно сохранен' });
                }
            });
        }
    });
});

// Получение данных пользователя
app.get('/user-data', authenticateToken, (req, res) => {
    const userId = req.user.userId;

    db.get('SELECT Имя, Почта, Стиль, Цвет, Материал, Рост, Размер_Одежды, Пол FROM Пользователи INNER JOIN Профили_Пользователей ON Пользователи.ID_Пользователя=Профили_Пользователей.ID_Пользователя WHERE Пользователи.ID_Пользователя = ?', [userId], (err, row) => {
        if (err) {
            console.error('Ошибка при получении данных пользователя:', err);
            return res.status(500).json({ error: 'Ошибка базы данных' });
        }

        if (!row) {
            return res.status(404).json({ error: 'Пользователь не найден' });
        }

        res.json({
            name: row.Имя,
            email: row.Почта,
            style: row.Стиль,
            color: row.Цвет,
            material: row.Материал,
            height: row.Рост,
            size: row.Размер_Одежды,
            gender: row.Пол
        });
    });
});

// Получение образов пользователя
app.get('/user-outfits', authenticateToken, async (req, res) => {
    const userId = req.user.userId;

    const query = `
        SELECT
            о.ID_Образа,
            о.Название,
            о.Параметры_Генерации,
            о.Дата_Создания,
            э.ID_Товара,
            т.Название AS Название_Товара,
            т.Ссылка_Товар,
            х.Ссылка_Изображение,
            э.Позиция
        FROM Образы о
                 LEFT JOIN Элементы_Образа э ON о.ID_Образа = э.ID_Образа
                 LEFT JOIN Товары т ON э.ID_Товара = т.ID_Товара
                 LEFT JOIN Характеристики_Товаров х ON т.ID_Товара = х.ID_Товара
        WHERE о.ID_Пользователя = ?
        ORDER BY о.Дата_Создания DESC, э.Позиция ASC
    `;

    db.all(query, [userId], (err, rows) => {
        if (err) {
            console.error('Ошибка при получении образов:', err.message);
            return res.status(500).json({ error: 'Ошибка базы данных' });
        }

        const outfitsMap = {};
        rows.forEach(row => {
            if (!outfitsMap[row.ID_Образа]) {
                outfitsMap[row.ID_Образа] = {
                    outfitId: row.ID_Образа,
                    outfitName: row.Название || 'Сохраненный образ',
                    generationParams: row.Параметры_Генерации,
                    creationDate: row.Дата_Создания,
                    products: []
                };
            }

            if (row.ID_Товара) {
                outfitsMap[row.ID_Образа].products.push({
                    productId: row.ID_Товара,
                    productName: row.Название_Товара,
                    productLink: row.Ссылка_Товар,
                    productImage: row.Ссылка_Изображение,
                    position: row.Позиция
                });
            }
        });

        const outfits = Object.values(outfitsMap);
        res.json(outfits);
    });
});

// Удаление образа
app.delete('/delete-outfit/:outfitId', authenticateToken, (req, res) => {
    const userId = req.user.userId;
    const outfitId = req.params.outfitId;

    // Проверяем, что образ принадлежит пользователю
    db.get('SELECT * FROM Образы WHERE ID_Образа = ? AND ID_Пользователя = ?',
        [outfitId, userId],
        (err, row) => {
            if (err) {
                console.error('Ошибка при проверке образа:', err.message);
                return res.status(500).json({ error: 'Ошибка базы данных' });
            }

            if (!row) {
                return res.status(404).json({ error: 'Образ не найден или у вас нет прав на его удаление' });
            }

            // Удаляем образ (внешние ключи настроены на каскадное удаление)
            db.run('DELETE FROM Образы WHERE ID_Образа = ?', [outfitId], function(err) {
                if (err) {
                    console.error('Ошибка при удалении образа:', err.message);
                    return res.status(500).json({ error: 'Ошибка удаления образа' });
                }

                res.json({ message: 'Образ успешно удален' });
            });
        }
    );
});

// Доступ к функциям авторизированных пользователей
app.get('/protected', authenticateToken, (req, res) => {
    res.json({ message: `Привет, ${req.user.username}! Это защищенный контент.` });
});

// Иницилизация сервера по порту 3000
const PORT = process.env.PORT
app.listen(PORT, () => {
    console.log(`✅ Server running on port ${PORT}`);
});
