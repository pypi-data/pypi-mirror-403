# datapipe

## Как залить на PyPI и пользоваться в других проектах

### Часть 1: Один раз залить пакет на PyPI

1. **Аккаунт на PyPI**Зарегистрируйтесь на [pypi.org](https://pypi.org) → Account → API tokens → Add API token. Скопируйте токен (он вида `pypi-...`).
2. **Автор в проекте**В файле `pyproject.toml` в блоке `[project]` замените:

   ```toml
   authors = [
       {name = "Ваше Имя", email = "your@email.com"}
   ]
   ```
3. **Сборка и загрузка**Откройте **CMD** в папке проекта `D:\projects\datapipe` и выполните:

   ```bat
   publish.bat
   ```

   Когда спросит логин: **Username** — `__token__`, **Password** — вставьте ваш API token.(Если PowerShell блокирует скрипты — используйте именно CMD и `publish.bat`.)
4. **Новые версии**
   Перед каждой следующей публикацией увеличьте версию в `pyproject.toml` и в `datapipe/__init__.py` (например, `0.1.1`), затем снова запустите `publish.bat`.

---

### Часть 2: Использовать в других проектах

В любом другом проекте (другая папка, другой репозиторий):

```bash
pip install datapipemath
```

В коде (импорт по‑прежнему `from datapipe import ...`):

```python
from datapipe import decomposition

decomposition()                           # одно плавное движение мыши
decomposition(max_offset=200, duration=0.5)  # со своими параметрами
```

Или из терминала: команда `datapipe` запускает бесконечный цикл (движение мыши + нажатие клавиши).

---

## Установка

```bash
pip install datapipemath
```

## Использование

## Требования

- Python 3.8+
- PyAutoGUI

## Лицензия

MIT
