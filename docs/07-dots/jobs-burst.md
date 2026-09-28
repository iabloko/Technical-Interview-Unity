[← К содержанию](../README.md)

# Job System и Burst

Часть DOTS, работают и без [ECS](ecs.md) (можно применять к обычному коду).

## Job System

Система многопоточности Unity для безопасного параллельного исполнения работы на всех ядрах CPU. В отличие от ручных [потоков](../01-csharp/multithreading.md), безопасность по данным проверяется движком.

Job — `struct`, реализующий интерфейс job'а, с методом `Execute`:

```csharp
[BurstCompile]
public struct AddJob : IJobParallelFor
{
    [ReadOnly]  public NativeArray<float> A;
    [ReadOnly]  public NativeArray<float> B;
    [WriteOnly] public NativeArray<float> Result;

    public void Execute(int i) => Result[i] = A[i] + B[i];
}

// планирование
var handle = job.Schedule(length, batchSize);
handle.Complete();   // дождаться результата
```

- `IJob` — одна задача; `IJobParallelFor` — разбивает диапазон по потокам.
- `Schedule` ставит job в очередь и возвращает `JobHandle`; зависимости связываются через handle'ы.
- Главный поток не блокируется до `Complete()`.

## Safety system

Job не может обращаться к управляемым объектам (классам, Unity API) — только к **blittable** данным в `NativeContainer`. Это и есть гарантия безопасности:

- `NativeArray<T>` (и `NativeList`, `NativeHashMap`…) — неуправляемая память с проверкой доступа. Требуют ручного `Dispose` (иначе утечка; есть `Allocator.Temp/TempJob/Persistent`).
- `T` должен быть unmanaged-типом (без ссылочных полей): `NativeArray<T>` объявлен с `where T : struct` и проверяет это в рантайме, контейнеры пакета Collections (`NativeList<T>` и др.) — ограничением `where T : unmanaged` (см. [generics](../01-csharp/generics.md)).
- Атрибуты `[ReadOnly]`/`[WriteOnly]` позволяют системе разрешать параллельный доступ; конфликтующая запись из двух job'ов отлавливается до запуска.

## Burst

Компилятор, транслирующий C#-подмножество job'ов в высокооптимизированный машинный код через LLVM, с автовекторизацией (SIMD). Включается атрибутом `[BurstCompile]`. Ускорение относительно обычного IL — кратное (часто ×10 и выше) на численных задачах.

Условия: Burst компилирует только blittable-данные и подмножество C# (без managed-объектов, исключений в общем случае, виртуальных вызовов). Поэтому Job + Burst + `NativeArray` идут вместе.

## Когда применять

- Тяжёлые **однородные численные** вычисления: симуляции, процедурная генерация, обработка вершин/частиц, AI на большом числе агентов.
- Не для разрозненной логики с обращениями к Unity API или managed-объектам.

## Что спрашивают на собеседовании

- Чем Job System безопаснее ручных потоков (проверка доступа к данным, `[ReadOnly]`/`[WriteOnly]`).
- Почему в job нельзя managed-объекты и Unity API (safety, blittable, `NativeArray`).
- Что делает Burst (LLVM, SIMD-векторизация) и при каких условиях.
- Зачем `Dispose` у `NativeArray` и что такое Allocator.
- Связка Job + Burst + NativeContainer и когда она оправдана.

---