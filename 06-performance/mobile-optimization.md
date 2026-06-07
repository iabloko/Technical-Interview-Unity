[← К содержанию](../README.md)

# Мобильная оптимизация

Мобильные GPU (tile-based deferred rendering, TBDR) и ограниченные CPU/память/тепло/батарея диктуют отдельные правила. Сначала определить, во что упёрлись (см. [методология профилирования](profiling-methodology.md)): CPU, GPU, память или fill-rate.

## GPU и fill-rate

- **Overdraw** — главный враг на мобиле. Полупрозрачность (particles, UI, alpha-blend) рисует одни пиксели многократно. TBDR плохо переносит overdraw. Минимизировать прозрачные слои, ограничивать размер частиц.
- **Разрешение** — fill-rate растёт квадратично. Динамическое разрешение / рендер в меньшем буфере.
- **Шейдеры дёшево.** Избегать тяжёлой математики на фрагмент, лишних сэмплов текстур; mobile-шейдеры URP.
- **Не очищать/не читать буферы зря.** На TBDR избегать `Blit`, чтения глубины, grab-pass без нужды; не отключать необдуманно framebuffer clear.

## Текстуры и память

- Сжатие **ASTC** (современный стандарт для мобил), не RGBA32.
- Mipmaps для всего, что в 3D (экономит bandwidth и убирает шум).
- Atlas'ы для UI и спрайтов (меньше [draw call'ов](batching.md)).
- Контроль через [Memory Profiler](../03-unity-core/memory-profiler.md): текстуры обычно — крупнейший потребитель памяти.

## CPU

- Минимум [draw call'ов](batching.md): SRP Batcher, instancing, атласы.
- Никакого мусора в кадре (см. [GC](../03-unity-core/unity-gc.md)): [пулы](../03-unity-core/object-pooling.md), без [LINQ](../01-csharp/linq.md)/замыканий в `Update`, кеш `GetComponent`.
- Физика: меньше [Raycast](../03-unity-core/physics.md), layer matrix, простые коллайдеры, разумный `fixedDeltaTime`.
- Тяжёлые вычисления — в [Job System + Burst](../07-dots/jobs-burst.md).

## Освещение

- Realtime-теней по минимуму; запекание света (baked GI, lightmaps) вместо realtime (см. [lighting](../04-rendering/lighting.md)).
- Few per-pixel lights; остальное — vertex/baked.

## Прочее

- Ограничить `Application.targetFrameRate` (30/60) — экономит батарею и тепло (троттлинг роняет FPS сильнее, чем кажется).
- Quality Settings / URP Asset на профиль под слабые устройства.
- Тестировать на **целевом устройстве**, не в редакторе — профиль производительности принципиально иной.

## Что спрашивают на собеседовании

- Что такое overdraw и почему он критичен на мобиле (TBDR, fill-rate).
- Какой формат сжатия текстур для мобил (ASTC) и зачем mipmaps.
- Как снижают CPU-нагрузку (draw calls, GC, физика).
- Почему профилировать надо на устройстве, а не в редакторе.

---