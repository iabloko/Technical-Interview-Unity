[← К содержанию](../README.md)

# Unity Profiler

Встроенный инструмент: **Window → Analysis → Profiler**. Записывает метрики игры **покадрово** и раскладывает их по модулям (CPU, GPU, Rendering, Memory, Physics, UI, Audio, Network). Главный инструмент для поиска *где* тормозит.

## Как работает

- Каждый кадр пишется в кольцевой буфер (по умолчанию ~300 кадров).
- На графике видно spike'и; кликнув по кадру, проваливаешься в иерархию вызовов с временем и аллокациями.
- В Editor цифры **приблизительные** (есть оверхед редактора). Для точных замеров — **Development Build** + *Autoconnect Profiler* или подключение к устройству по сети/USB.
- **Deep Profile** — профилирует **каждый** метод (детально, но медленно; включается только для коротких сессий).
- Свои регионы в коде — через `ProfilerMarker`:

```csharp
private static readonly ProfilerMarker _aiMarker = new("AI.Tick");

void Update()
{
    using (_aiMarker.Auto())  // блок будет виден отдельной строкой в Profiler
    {
        _ai.Tick();
    }
}
```

## Что ключевое можно посмотреть

- **Время кадра** и его разбивка: CPU main thread, render thread, GPU — где «узкое место».
- **Колонка `GC Alloc`** в CPU-иерархии — кто и сколько аллоцирует в куче (скрытые `new`, boxing, LINQ, лямбды). Прямая причина GC-спайков.
- **Draw calls / SetPass calls / Batches** в Rendering-модуле — эффективность батчинга и SRP Batcher.
- **Physics**: стоимость симуляции и `FixedUpdate`.
- **Scripts**: иерархия `Update`/`LateUpdate`/`Coroutines`, время на каждом скрипте.
- **Memory** (упрощённо): managed/native, текстуры, меши, аудио. Для глубокого анализа — отдельный *Memory Profiler*.
---