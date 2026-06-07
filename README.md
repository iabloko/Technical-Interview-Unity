# Technical-Interview-Unity

База знаний для подготовки к техническому собеседованию по **Unity / C#**.

## Содержание

### 01. C#
- [ООП](01-csharp/oop.md)
- [Управляемая и неуправляемая память](01-csharp/managed-unmanaged-memory.md)
- [Стек и куча](01-csharp/stack-heap.md)
- [Boxing / Unboxing](01-csharp/boxing-unboxing.md)
- [Делегаты, события, Action / Func, замыкания](01-csharp/delegates-events.md)
- [Коллекции и сложность операций](01-csharp/collections.md)
- [Многопоточность и синхронизация](01-csharp/multithreading.md)
- [Span / Memory / ref struct / stackalloc](01-csharp/span-memory.md)
- [LINQ: отложенное выполнение и аллокации](01-csharp/linq.md)
- [Равенство: Equals / GetHashCode / IEquatable](01-csharp/equality.md)
- [Обобщения: ограничения и вариантность](01-csharp/generics.md)
- [Современный C#: record, pattern matching, switch expressions](01-csharp/modern-csharp.md)

### 02. Архитектура и паттерны
- [SOLID](02-architecture/solid.md)
- [Лучшие практики (DRY / KISS)](02-architecture/best-practices.md)
- [Связанность (coupling / decoupling)](02-architecture/coupling-decoupling.md)
- [Dependency Injection (Zenject)](02-architecture/di.md)

### 03. Ядро Unity
- [Жизненный цикл MonoBehaviour](03-unity-core/lifecycle.md)
- [Unity Garbage Collector](03-unity-core/unity-gc.md)
- [Загрузка ассетов: Resources / AssetBundles / Addressables](03-unity-core/asset-management.md)
- [Profiler](03-unity-core/profiler.md)
- [Frame Debugger](03-unity-core/frame-debugger.md)
- [Memory Profiler](03-unity-core/memory-profiler.md)
- [Scripting backend: Mono vs IL2CPP, AOT vs JIT](03-unity-core/il2cpp-mono.md)
- [Сериализация в Unity](03-unity-core/serialization.md)
- [ScriptableObject](03-unity-core/scriptable-object.md)
- [Физика](03-unity-core/physics.md)
- [Assembly Definitions (.asmdef)](03-unity-core/assembly-definitions.md)
- [Object Pooling](03-unity-core/object-pooling.md)
- [Префабы: variants и nested](03-unity-core/prefabs.md)

### 04. Рендеринг
- [Графический конвейер (этапы построения изображения)](04-rendering/graphics-pipeline.md)
- [URP — Universal Render Pipeline](04-rendering/urp-render-pipeline.md)
- [Освещение: URP vs Built-in](04-rendering/lighting.md)

### 05. Асинхронность
- [Task / IEnumerator / UniTask](05-async/async.md)

### 06. Производительность
- [Батчинг draw call'ов: Static/Dynamic, SRP Batcher, GPU Instancing](06-performance/batching.md)
- [Мобильная оптимизация](06-performance/mobile-optimization.md)
- [Методология профилирования](06-performance/profiling-methodology.md)

### 07. DOTS
- [ECS (Entity Component System)](07-dots/ecs.md)
- [Job System и Burst](07-dots/jobs-burst.md)

### 08. Паттерны
- [Паттерны проектирования в Unity](08-patterns/design-patterns.md)
- [Конечный автомат (FSM)](08-patterns/fsm.md)
- [Презентационные паттерны: MVC / MVP / MVVM](08-patterns/mvp-mvvm.md)

### 09. Тестирование
- [Unity Test Framework](09-testing/testing.md)

### 10. Математика
- [Векторы, кватернионы, матрицы](10-math/math.md)

---