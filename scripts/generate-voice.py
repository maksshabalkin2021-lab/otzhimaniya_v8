"""
Генератор голосовых клипов для "Счёт отжиманий".

Проходит по списку фраз (единый источник правды — тексты должны ТОЧНО совпадать
с тем, что передаётся в say() в www/index.html), генерирует mp3 через edge-tts
(бесплатный, без API-ключа, использует голосовой движок Microsoft Edge) для двух
русских голосов и пишет manifest.json.

Запуск: pip install edge-tts && python scripts/generate-voice.py
Результат: www/vendor/voice/{dmitry,svetlana}/*.mp3 + www/vendor/voice/manifest.json

Если файл уже существует — генерация пропускается (можно безопасно перезапускать
и дополнять список фраз).
"""
import asyncio
import json
import os

import edge_tts

VOICES = {
    "dmitry": "ru-RU-DmitryNeural",
    "svetlana": "ru-RU-SvetlanaNeural",
}

# Точные строки, передаваемые в say() по всему www/index.html.
PHRASES = [
    # отсчёт перед стартом
    "Три", "Два", "Один", "Погнали, жми!",
    # отсчёт перед концом отдыха (нижний регистр, отдельные вызовы в коде)
    "один", "два", "три",
    # SAY_REST / SAY_REST_HYPE / SAY_REST_BEAST
    "Отдых.", "Передышка.", "Дыши.",
    "Красава, отдых!", "Мощно! Передышка.", "Есть подход! Дыши.",
    "Зверь! Отдыхай!", "Огонь! Дыши, боец!", "Машина! Передышка!",
    # SAY_GO / SAY_GO_BEAST
    "Погнали!", "Вперёд!", "Поехали, жми!",
    "В бой!", "Рви! Погнали!", "Жми до отказа!",
    # SAY_GOAL / SAY_GOAL_BEAST
    "Цель!", "Есть!", "Взял!",
    "Цель взята! Огонь!", "Есть! Зверюга!", "Красавчик! Цель!",
    # SAY_DONE
    "Тренировка завершена. Красавчик!", "Готово! Машина!", "Всё! Зверь! Так держать!",
    # разминка / тест / рекорд
    "Разминка. Береги плечи!",
    "День теста. Жми максимум!",
    "Новый рекорд! Огонь!",
    # подбадривание (cheerLead 1..8)
    "Последний!", "Ещё два!", "Ещё три!", "Ещё четыре!",
    "Ещё пять!", "Ещё шесть!", "Ещё семь!", "Ещё восемь!",
    # темп
    "Вниз", "Вверх",
    # тумблеры настроек
    "Поехали! Погнали!",
    "Три, два, один, погнали!",
    "Буду подсказывать хват на каждый подход.",
    # хваты (шаблонные фразы, gripForSet(0) всегда классический на первом подходе)
    "Первый подход — классический хват.",
    "Отдых. Следующий подход — классический хват.",
    "Отдых. Следующий подход — широкий хват.",
    "Отдых. Следующий подход — узкий, алмазный хват.",
    "Отдых. Следующий подход — на кулаках.",
]
# убрать дубликаты, сохранив порядок
PHRASES = list(dict.fromkeys(PHRASES))

NUMBERS = list(range(1, 201))  # покрывает макс. цель свободного режима (200) и подхода программы (65)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOICE_DIR = os.path.join(ROOT, "www", "vendor", "voice")

SEM = asyncio.Semaphore(8)


async def gen_one(text, voice_id, out_path):
    if os.path.exists(out_path):
        return
    async with SEM:
        for attempt in range(3):
            try:
                comm = edge_tts.Communicate(text, voice_id)
                await comm.save(out_path)
                return
            except Exception as e:
                if attempt == 2:
                    print(f"FAILED after 3 tries: {text!r} ({voice_id}): {e}")
                else:
                    await asyncio.sleep(1.5)


async def main():
    manifest = {"phrases": {}, "numbers": {}}
    tasks = []

    for i, text in enumerate(PHRASES):
        fname = f"p{i:03d}.mp3"
        manifest["phrases"][text] = fname
        for vid, voice in VOICES.items():
            out_dir = os.path.join(VOICE_DIR, vid)
            os.makedirs(out_dir, exist_ok=True)
            tasks.append(gen_one(text, voice, os.path.join(out_dir, fname)))

    for n in NUMBERS:
        fname = f"n{n}.mp3"
        manifest["numbers"][str(n)] = fname
        for vid, voice in VOICES.items():
            out_dir = os.path.join(VOICE_DIR, vid)
            os.makedirs(out_dir, exist_ok=True)
            tasks.append(gen_one(str(n), voice, os.path.join(out_dir, fname)))

    total = len(tasks)
    done = 0
    CHUNK = 40
    for i in range(0, total, CHUNK):
        chunk = tasks[i:i + CHUNK]
        await asyncio.gather(*chunk)
        done += len(chunk)
        print(f"{done}/{total}")

    os.makedirs(VOICE_DIR, exist_ok=True)
    with open(os.path.join(VOICE_DIR, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=0)

    print(f"Done. {len(PHRASES)} phrases + {len(NUMBERS)} numbers x {len(VOICES)} voices.")


if __name__ == "__main__":
    asyncio.run(main())
