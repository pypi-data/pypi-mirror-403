# Rodina Forum API Async

[![PyPI version](https://img.shields.io/pypi/v/rodina-forum-api-async.svg)](https://pypi.org/project/rodina-forum-api-async/)
[![Python Versions](https://img.shields.io/pypi/pyversions/rodina-forum-api-async.svg)](https://pypi.org/project/rodina-forum-api-async/)
[![Downloads](https://static.pepy.tech/badge/rodina-forum-api-async)](https://pepy.tech/project/rodina-forum-api-async)

**Асинхронная Python библиотека для взаимодействия с форумом Rodina RP (forum.rodina-rp.com) без необходимости получения API ключа.**

Эта библиотека предоставляет современный, асинхронный интерфейс для работы с форумом Rodina RP. Это изменённая под Родину версия оригинальной библиотеки [Arizona-Forum-API-Async](https://github.com/fakelag28/Arizona-Forum-API-Async), построенная с использованием `aiohttp`.

---

## Ключевые особенности

*   **Полностью асинхронная:** Построена с использованием `asyncio` и `aiohttp`.
*   **Не требует API ключа:** Взаимодействует с форумом, имитируя запросы браузера, что избавляет от необходимости получать официальные ключи XenForo API.
*   **Обширная функциональность:** Поддерживает около 38 методов.
*   **Объектно-ориентированные модели:** Представляет сущности форума, такие как `Member`, `Thread`, `Post`, `Category`, в виде Python объектов с соответствующими методами.
*   **Простота использования:** Предоставляет чистую и интуитивно понятную структуру API.

---

## Установка

Установите библиотеку напрямую из PyPI:

```bash
pip install rodina-forum-api-async
```

---

## Аутентификация и настройка

Поскольку эта библиотека имитирует действия залогиненного пользователя, вам потребуются две вещи из вашей браузерной сессии на `forum.rodina-rp.com`:

1.  **User Agent:** Строка User Agent вашего браузера.
2.  **Cookies:** Cookies вашей сессии на форуме.

**Как их получить:**

1.  Войдите в свой форумный аккаунт на `forum.rodina-rp.com`.
2.  Установите расширение "Cookie Editor", после чего с его помощью получите следующие значения:
* xf_session
* xf_tfa_trust
* xf_user
3. Узнайте свой User Agent браузера или используйте любые другие из интернета.

---

## Документация и примеры

*   **[Папка с примерами](https://github.com/fakelag28/Rodina-Forum-API-Async/tree/main/examples):** Практические примеры, демонстрирующие различные возможности библиотеки.

---

## Лицензия

Этот проект лицензирован под **MIT License**.