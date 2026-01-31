# UTM-триггеры - Краткая инструкция

## Что это?

UTM-триггеры отправляют специальное сообщение пользователям, которые переходят по ссылке с определенными UTM-метками. При совпадении стандартная логика `/start` пропускается.

## Быстрый старт

### 1. Создайте файл с сообщением

Создайте папку и файл:
```
bots/ваш_bot_id/utm_message/vk_campaign.txt
```

Содержимое файла:
```
Привет! Вы перешли по ссылке из ВКонтакте! 🎉
```

### 2. Зарегистрируйте триггер

В файле запускалки (например, `mdclinica.py`):

```python
"""my-bot.py"""
import asyncio
from smart_bot_factory.creation import BotBuilder

# Инициализация
bot_builder = BotBuilder("my-bot")

# =============================================================================
# UTM-ТРИГГЕРЫ
# =============================================================================

bot_builder.register_utm_trigger(
    message='vk_campaign.txt',  # Файл из bots/my-bot/utm_message/
    source='vk',                 # utm_source должен быть 'vk'
    campaign='summer2025'        # utm_campaign должен быть 'summer2025'
)

async def main():
    await bot_builder.build()
    await bot_builder.start()

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. Создайте UTM-ссылку

```
https://t.me/your_bot?start=source-vk_campaign-summer2025
```

## Параметры

- `message` - имя файла (обязательно)
- `source`, `medium`, `campaign`, `content`, `term`, `segment` - значения UTM-меток

## Примеры использования

```python
# Для кампании
bot_builder.register_utm_trigger(
    message='summer.txt',
    source='vk',
    campaign='summer2025'
)

# Для сегмента
bot_builder.register_utm_trigger(
    message='premium.txt',
    segment='premium'
)

# С несколькими параметрами
bot_builder.register_utm_trigger(
    message='new_year.txt',
    source='instagram',
    medium='story',
    campaign='new_year'
)
```

## Важно

- Файлы в `bots/ваш_bot_id/utm_message/`
- Регистрация триггеров **ДО** `bot_builder.register_routers()`
