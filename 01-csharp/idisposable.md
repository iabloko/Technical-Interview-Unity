[← К содержанию](../README.md)

# IDisposable, using и освобождение ресурсов

`IDisposable` — контракт **детерминированного** освобождения ресурса: вызывающий сам решает, *когда* ресурс будет освобождён, не дожидаясь [GC](../03-unity-core/unity-gc.md). Нужен, когда объект держит то, что GC освободить не умеет или освободит слишком поздно: неуправляемые хендлы, подписки на события, таймеры, `CancellationTokenSource`, `NativeArray<T>`.

> Базовый контекст «управляемое vs неуправляемое» и полный Dispose-паттерн с финализатором — в [управляемой памяти](managed-unmanaged-memory.md). Здесь — семантика `using`, `IAsyncDisposable`, владение и типичные ошибки.

## Контракт

```csharp
public interface IDisposable
{
    void Dispose();
}
```

Гарантий, которые должен соблюдать корректный `Dispose`:

- **Идемпотентность.** Повторный вызов `Dispose()` не должен бросать и не должен ничего ломать (флаг `_disposed`).
- **Не бросать исключений** из `Dispose`, кроме критических. Исключение из `Dispose` в блоке `using`, выполняющемся при раскрутке другого исключения, **затирает** исходное.
- После `Dispose` объект считается непригодным: публичные методы вправе бросать `ObjectDisposedException`.

## `using`: statement vs declaration

`using` — синтаксический сахар над `try/finally` с вызовом `Dispose()` в `finally` (см. [исключения](exceptions.md)). `Dispose` вызовется при любом выходе: нормальном, через `return`, через исключение.

```csharp
// using-statement — явный блок, ресурс живёт ровно в фигурных скобках
using (var stream = File.OpenRead(path))
{
    Read(stream);
}   // Dispose() здесь

// using-declaration (C# 8+) — освобождение в конце ОБЪЕМЛЮЩЕЙ области
void Process()
{
    using var stream = File.OpenRead(path);
    Read(stream);
}   // Dispose() в конце метода
```

Разница в **сроке жизни**: declaration удобнее, но ресурс держится до конца метода. Если нужно освободить раньше (например, закрыть файл до долгой обработки) — явный `using`-блок.

Несколько ресурсов освобождаются в **обратном** порядке захвата (LIFO):

```csharp
using var a = new A();
using var b = new B();   // Dispose: сначала b, потом a
```

## Структуры и `ref struct`

Для обычных `class` и `struct` `using` требует реализации `IDisposable`. Исключение — `ref struct` (C# 8+): до C# 13 они **не могут** реализовывать интерфейсы, поэтому для них компилятор принимает доступный метод `void Dispose()` без интерфейса (pattern-based dispose) — в `using` и в `foreach` (кастомные enumerator'ы). Освобождение `struct`, реализующего `IDisposable`, через `using` не боксит: компилятор генерирует constrained-вызов `Dispose()`.

## IAsyncDisposable / await using

Когда освобождение само асинхронно (сброс буфера в сеть, закрытие соединения), синхронный `Dispose` либо блокирует поток, либо делает fire-and-forget. Для этого — `IAsyncDisposable`:

```csharp
public interface IAsyncDisposable
{
    ValueTask DisposeAsync();
}

await using var conn = new DbConnection();   // DisposeAsync() в конце области
await conn.QueryAsync();
```

- Возвращает `ValueTask` — чтобы не аллоцировать на синхронно завершённом освобождении (см. [async-внутренности](../05-async/async-internals.md)).
- Тип может реализовывать **оба** интерфейса; `await using` предпочитает `DisposeAsync`.
- В Unity актуально реже (нет `await using` в большинстве gameplay-кода), но встречается в сетевых/IO-обёртках.

## Владение (ownership)

Главный вопрос на собеседовании: **кто обязан звать `Dispose`?** Тот, кто ресурсом **владеет** — обычно тот, кто его создал.

```csharp
// Передали готовый stream — НЕ наш, не диспозим (закроем чужой ресурс под ногами)
public Parser(Stream input) => _input = input;

// Создали сами — наши, обязаны освободить в своём Dispose
public Parser(string path) { _input = File.OpenRead(path); _owns = true; }
public void Dispose() { if (_owns) _input.Dispose(); }
```

- **Коллекция disposable-объектов** не диспозит элементы автоматически — это делает владелец вручную в цикле.
- **DI-контейнеры** (Zenject/VContainer, см. [DI](../02-architecture/di.md)) часто берут владение на себя: объект, зарегистрированный как `IDisposable` в скоупе, контейнер освобождает при разрушении скоупа. Двойной `Dispose` (и контейнером, и вручную) — поэтому идемпотентность обязательна.

## Специфика Unity

- **`MonoBehaviour` не использует `IDisposable`** — у него свой жизненный цикл (`OnDestroy`, см. [lifecycle](../03-unity-core/lifecycle.md)). Освобождение чего-либо disposable у компонента вешают на `OnDestroy`/`OnDisable`, а не на `using`.
- **`CancellationTokenSource`** — `IDisposable`; забытый `Dispose` течёт (внутренние таймеры/линки). Создал CTS вручную — освободи в `OnDestroy`.
- **`NativeArray<T>` и `Unity.Collections`** — `IDisposable`; без `Dispose` (или без авто-`Allocator`) — утечка нативной памяти, ловится Leak Detection.
- **Подписки** (UniRx/R3 `IDisposable` из `Subscribe`, см. [UniRx](../11-tools/unirx.md)) собирают в `CompositeDisposable`/`.AddTo(this)`, чтобы массово освободить при уничтожении объекта.
- **Addressables-хендлы** — это **не** `IDisposable`; их освобождают `Addressables.Release(handle)`, не `using` (см. [addressables](../03-unity-core/addressables.md)). Частая путаница.

## Что спрашивают на собеседовании

- Зачем `IDisposable`, если есть GC? (Детерминированное освобождение **сейчас**, а не когда-нибудь; неуправляемые ресурсы GC не освобождает.)
- В какой момент вызывается `Dispose` при `using` и при исключении внутри? (`finally`, всегда — это `try/finally`.)
- Разница `using`-statement и `using`-declaration. (Срок жизни: блок vs конец области.)
- Почему `Dispose` должен быть идемпотентным и не бросать? (Двойной вызов из DI/повторный код; исключение из Dispose затирает исходное при раскрутке.)
- Зачем `IAsyncDisposable`, если есть `IDisposable`? (Асинхронное освобождение без блокировки потока; `ValueTask`.)
- Кто обязан звать `Dispose` при передаче ресурса в чужой объект? (Владелец — обычно создатель; не диспозить чужой переданный ресурс.)
- Может ли `ref struct` реализовать `IDisposable`? (До C# 13 — нет; `using` принимает у `ref struct` метод `Dispose()` без интерфейса.)

---