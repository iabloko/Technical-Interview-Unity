[← К содержанию](../README.md)

# Async/await: внутреннее устройство

Эта заметка — про **механику** `async/await`: во что компилятор разворачивает метод, что такое awaiter, как работает `SynchronizationContext`, откуда берутся дедлоки и зачем `ConfigureAwait`. Сравнение `Task` / корутин / `UniTask` и Unity-практику — в [асинхронности](async.md).

## Что генерирует компилятор

`async`-метод компилируется в **конечный автомат (state machine)** — сгенерированную структуру, реализующую `IAsyncStateMachine`. Тело метода переписывается в один метод `MoveNext()`, где каждый `await` — это точка возможной приостановки и точка возобновления.

```csharp
async Task<int> GetAsync()
{
    int a = await StepA();   // состояние 0
    int b = await StepB(a);  // состояние 1
    return a + b;
}
```

Упрощённо разворачивается в:

```csharp
struct GetAsyncStateMachine : IAsyncStateMachine
{
    public int State;
    public AsyncTaskMethodBuilder<int> Builder;   // создаёт/завершает Task
    private TaskAwaiter<int> _awaiter;
    private int _a;

    public void MoveNext()
    {
        switch (State)
        {
            case -1:                         // первый вход
                _awaiter = StepA().GetAwaiter();
                if (!_awaiter.IsCompleted)   // ещё не готово — приостановиться
                {
                    State = 0;
                    Builder.AwaitUnsafeOnCompleted(ref _awaiter, ref this); // регистрируем continuation
                    return;                  // управление возвращается вызывающему
                }
                goto case 0;
            case 0:
                _a = _awaiter.GetResult();   // забрать результат / пробросить исключение
                // ... аналогично для StepB
                break;
        }
    }
}
```

Ключевые следствия:

- **До первого «незавершённого» `await` метод выполняется синхронно**, в потоке вызывающего. `async` не делает код параллельным сам по себе.
- На приостановке регистрируется **continuation** (продолжение), а управление возвращается вызывающему. Метод «возобновится» вызовом `MoveNext` из awaiter'а, когда ожидаемое завершится.
- **Builder** создаёт возвращаемый `Task`/`ValueTask`/`UniTask` и завершает его результатом или исключением.

## Паттерн awaitable / awaiter

`await` работает не только с `Task`, а с **любым типом, у которого есть метод `GetAwaiter()`**, возвращающий awaiter с тремя членами:

```csharp
public struct MyAwaiter : INotifyCompletion
{
    public bool IsCompleted { get; }              // уже готово? тогда не приостанавливаемся
    public void OnCompleted(Action continuation);  // как зарегистрировать продолжение
    public T GetResult();                          // результат или проброс исключения
}
```

Именно поэтому можно `await` `Task`, `ValueTask`, `UniTask`, `YieldAwaitable`, `AsyncOperation` (в UniTask) — все они дают awaiter. Это «duck typing» на уровне компилятора, не интерфейс.

## SynchronizationContext: куда возвращается continuation

После `await` код (continuation) должен где-то выполниться. По умолчанию `await` захватывает текущий **`SynchronizationContext`** (или `TaskScheduler`) и публикует продолжение в него.

- **UI-приложения / Unity**: есть контекст, который маршалит continuation обратно в **главный поток**. Поэтому после `await` обычно безопасно трогать Unity API.
- **Пул потоков / сервер**: контекста нет (`null`) — continuation выполнится на произвольном потоке пула.
- В Unity это `UnitySynchronizationContext`, установленный на главном потоке. Стоит реальных накладных расходов на маршалинг — одна из причин, по которой `UniTask` идёт мимо него, прямо через **PlayerLoop** (см. [async](async.md)).

## Дедлок на `.Result` / `.Wait()`

Классическая ошибка senior-уровня. На потоке с однопоточным `SynchronizationContext` (UI-поток, главный поток Unity):

```csharp
// главный поток
int x = GetAsync().Result;   // блокируем главный поток в ожидании Task
```

Внутри `GetAsync` после `await` continuation хочет вернуться **в главный поток** через захваченный контекст. Но главный поток **заблокирован** на `.Result` и никогда не освободится, чтобы выполнить continuation → взаимная блокировка.

- **Правило: не блокировать async-код** через `.Result` / `.Wait()` / `GetAwaiter().GetResult()` на потоке с контекстом. Только `await` по всей цепочке («async all the way»).
- Разорвать (для библиотечного кода) можно `ConfigureAwait(false)` — но это лечит симптом.

## ConfigureAwait(false)

`ConfigureAwait(false)` говорит awaiter'у **не** захватывать `SynchronizationContext` — continuation выполнится на потоке пула, а не возвращается в исходный.

```csharp
var data = await client.GetAsync(url).ConfigureAwait(false);
// здесь мы уже НЕ гарантированно в исходном потоке
```

- **Библиотечный / Domain-код** без привязки к UI: `ConfigureAwait(false)` уместен — меньше маршалинга, нет риска дедлока.
- **Unity gameplay-код**: обычно **не** нужен и опасен — после него можно оказаться **не** в главном потоке, и обращение к Unity API упадёт. Для `UniTask` вопрос неактуален: оно про PlayerLoop, а не про SynchronizationContext.

## Task vs ValueTask

`Task<T>` — **класс** (аллокация в куче) на каждый вызов. Если метод часто завершается **синхронно** (кэш-попадание, готовые данные), это лишний мусор в [GC](../03-unity-core/unity-gc.md).

```csharp
public ValueTask<int> GetAsync()
{
    if (_cache.TryGetValue(key, out var v))
        return new ValueTask<int>(v);     // 0 аллокаций на синхронном пути
    return new ValueTask<int>(LoadAsync()); // оборачивает Task на асинхронном
}
```

- `ValueTask<T>` — **struct**: ноль аллокаций, когда результат готов синхронно.
- Ограничения: **нельзя await дважды**, нельзя `.Result` до завершения, нельзя хранить/делить. Для повторного использования — `.AsTask()`.
- Поэтому `ValueTask` — оптимизация горячих путей, а не дефолт вместо `Task`. (`UniTask` решает ту же задачу аллокаций в Unity радикальнее — он struct всегда.)

## Где живёт исключение

Исключение из `async`-метода **не вылетает наружу сразу** — builder помещает его в возвращаемый `Task`, и оно всплывает при `await` (или при обращении к `.Result`, обёрнутое в `AggregateException`).

- У `async void` исключение **некуда положить** — builder публикует его в `SynchronizationContext` как необработанное: в Unity `UnitySynchronizationContext` его логирует, без контекста (пул потоков) оно завершает процесс. Вызывающий код перехватить его не может. Отсюда правило «`async void` только для обработчиков событий», а в Unity — `UniTaskVoid` + `.Forget()` (см. [исключения](../01-csharp/exceptions.md), [async](async.md)).
- Отмена через `CancellationToken` бросает `OperationCanceledException` — это **штатный** поток, а не ошибка; Task переходит в состояние `Canceled`.

## Что спрашивают на собеседовании

- Во что компилируется `async`-метод? (Конечный автомат `IAsyncStateMachine` с `MoveNext`; каждый `await` — точка приостановки/возобновления.)
- Выполняется ли начало `async`-метода синхронно? (Да — до первого незавершённого `await`, в потоке вызывающего.)
- Что должен иметь тип, чтобы его можно было `await`? (`GetAwaiter()` → awaiter с `IsCompleted` / `OnCompleted` / `GetResult`.)
- Что такое `SynchronizationContext` и зачем он в Unity? (Маршалит continuation в главный поток; есть `UnitySynchronizationContext`.)
- Почему `task.Result` на главном потоке вешает приложение? (Continuation ждёт главный поток, а он заблокирован — дедлок.)
- Что делает `ConfigureAwait(false)` и когда он опасен в Unity? (Не захватывает контекст; после него можно быть не в главном потоке.)
- Чем `ValueTask` отличается от `Task` и когда он оправдан? (Struct, 0 аллокаций на синхронном пути; нельзя await дважды; для горячих путей.)
- Куда попадает исключение из `async`-метода? (В возвращаемый Task, всплывает на `await`; из `async void` — в `SynchronizationContext`: в Unity логируется, без контекста завершает процесс.)

---