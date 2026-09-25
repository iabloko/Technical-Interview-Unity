[← К содержанию](../README.md)

# Асинхронность: Task, IEnumerator (корутины), UniTask

## Часть 1. Что такое асинхронное программирование

**Асинхронность** — способ выполнять операцию, не блокируя поток на время её ожидания. Поток не «стоит» в ожидании ответа сети или истечения таймера, а **освобождается** и возвращается к работе, когда результат готов.

Ключевая причина в Unity: **игровой код исполняется в одном (главном) потоке**, и любая блокировка этого потока = фриз кадра. Если синхронно ждать загрузку ассета или ответ сервера — игра замёрзнет. Асинхронность позволяет «отпустить» кадр и продолжить логику позже.

> **Асинхронность ≠ многопоточность.** Async — про *ожидание без блокировки* (может работать в одном потоке, перемежая задачи). Многопоточность — про *параллельное исполнение* на разных ядрах. В Unity большинство async-кода живёт в **одном** главном потоке: пока ждём — отдаём кадр движку, не уходя в другой поток (Unity API не потокобезопасен, см. [мьютекс](../01-csharp/glossary.md#мьютекс)).

### Как работает `async/await`

`async/await` — это синтаксический сахар: компилятор разворачивает метод в **конечный автомат (state machine)**. На каждом `await` метод «приостанавливается», сохраняя своё состояние, и регистрирует **continuation** — продолжение, которое выполнится, когда ожидаемое завершится. Управление в этот момент возвращается вызывающему коду.

```csharp
async Task LoadAsync()
{
    Show("loading...");          // выполняется сразу
    var data = await Fetch();    // здесь метод "ставится на паузу", кадр отдаётся движку
    Show(data);                  // continuation: выполнится, когда Fetch завершится
}
```

Куда вернётся continuation — определяет **SynchronizationContext**. В Unity есть `UnitySynchronizationContext`, который возвращает продолжение в **главный поток** — поэтому после `await` обычно можно безопасно трогать `transform` и прочее Unity API.

---

## Часть 2. Три инструмента в Unity

В Unity исторически сосуществуют три механизма «отложенного» кода. Важно понимать сильные и слабые стороны каждого.

### IEnumerator — корутины

Кооперативная многозадачность поверх итераторов C#. Корутину запускает MonoBehaviour (`StartCoroutine`), движок «прокручивает» её на определённых [точках кадра](../03-unity-core/lifecycle.md) (`yield return`).

```csharp
IEnumerator Blink()
{
    for (int i = 0; i < 3; i++)
    {
        _sprite.enabled = false;
        yield return new WaitForSeconds(0.2f);  // пауза, продолжит через 0.2с
        _sprite.enabled = true;
        yield return new WaitForSeconds(0.2f);
    }
}
StartCoroutine(Blink());
```

- **Плюсы:** просты, встроены, привязаны к жизни объекта: `SetActive(false)` на GameObject и `Destroy` останавливают все его корутины (при повторной активации они не продолжаются); `enabled = false` у компонента корутины **не** останавливает.
- **Минусы:**
  - **нет возвращаемого значения** (только `yield`), композиция громоздкая;
  - **исключения не пробрасываются** вызывающему коду: Unity логирует исключение и завершает корутину, запустивший её код об ошибке не узнаёт;
  - **аллокации** — `new WaitForSeconds(...)` и сам энумератор аллоцируются в куче (нагрузка на [GC](../03-unity-core/unity-gc.md));
  - запускаются только через MonoBehaviour на активном GameObject (`StartCoroutine`), из обычного C#-класса не запустить;
  - нельзя `await`, неудобно отменять выборочно.

### Task — стандартный .NET TPL

`System.Threading.Tasks.Task` — родной асинхронный примитив .NET. Создан в первую очередь для **IO** и **работы в пуле потоков**, не под игровой цикл Unity.

```csharp
private static readonly HttpClient Client = new HttpClient(); // один экземпляр на приложение: клиент на каждый запрос удерживает сокеты

async Task<string> DownloadAsync(string url)
{
    return await Client.GetStringAsync(url);   // IO-операция, не блокирует поток
}
```

- **Плюсы:** стандарт индустрии; работает с любыми .NET-библиотеками; пробрасывает исключения; `CancellationToken`; легко уйти в пул потоков (`Task.Run`) для CPU-работы.
- **Минусы в Unity:**
  - **аллоцирует** — `Task`/`Task<T>` это **класс** (объект в куче) + бокс state machine → мусор в GC на каждый вызов;
  - **не знает про кадры/PlayerLoop** — нельзя «подождать кадр» или `WaitUntil` нативно;
  - continuation идёт через `SynchronizationContext`, что даёт накладные расходы и легко «потерять» главный поток через `ConfigureAwait(false)`;
  - `Task.Run` уходит в **другой поток** — там **нельзя** трогать Unity API.

### UniTask — async для Unity (Cysharp)

`UniTask` — замена `Task` и корутин, спроектированная под Unity. Это **struct-based** awaitable: ноль аллокаций в куче на типичных путях, исполнение на **PlayerLoop** (а не через SynchronizationContext), нативная интеграция с кадрами и Unity-операциями.

```csharp
async UniTask LoadLevelAsync(CancellationToken ct)
{
    await UniTask.Delay(200, cancellationToken: ct);      // пауза без аллокаций
    await UniTask.Yield(PlayerLoopTiming.Update);          // подождать кадр
    var handle = Addressables.LoadAssetAsync<GameObject>("Boss");
    var prefab = await handle.ToUniTask(cancellationToken: ct);  // handle освобождают Addressables.Release(handle), когда ассет не нужен
    await UniTask.WaitUntil(() => _ready, cancellationToken: ct);
}
```

- **Плюсы:** zero-allocation; работает из любого C#-класса (не нужен MonoBehaviour); умеет ждать кадры/тайминги PlayerLoop; оборачивает `AsyncOperation`, `Addressables`, `UnityWebRequest`, `DOTween` (`.ToUniTask()`); хорошая отмена через `CancellationToken`, привязка к жизни объекта (`GetCancellationTokenOnDestroy()`); удобные `UniTask.WhenAll/WhenAny`.
- **Минусы:** внешняя зависимость (не из коробки); UniTask можно `await` **только один раз**: источник результата (`IUniTaskSource`) берётся из пула и после первого `GetResult` возвращается в пул (повторно — через `.Preserve()` или `AsyncLazy`).

---

## Часть 3. Чем `Task` отличается от `UniTask`

| | `Task` / `Task<T>` | `UniTask` / `UniTask<T>` |
|---|---|---|
| Тип | **class** (аллокация в куче) | **struct** (0 аллокаций на типичном пути) |
| Где исполняется | пул потоков + `SynchronizationContext` | **PlayerLoop** Unity (главный поток) |
| Кадры/тайминги | не умеет нативно | `Yield`, `DelayFrame`, `WaitUntil`, `NextFrame` |
| Unity-операции | вручную оборачивать | `.ToUniTask()` для `AsyncOperation`/Addressables/WebRequest |
| Сколько раз await | многократно | **один раз** (`.Preserve()` чтобы повторно) |
| Отмена | `CancellationToken` | `CancellationToken` + привязка к lifecycle объекта |
| Совместимость | стандарт .NET, любые библиотеки | конверсии `ToUniTask()` / `AsTask()` |
| GC-нагрузка | заметная (объект + бокс) | минимальная |

> Коротко: `Task` — универсальный .NET-примитив, не знающий про Unity и аллоцирующий в куче. `UniTask` — спроектирован под игровой цикл Unity, не аллоцирует и понимает кадры. Внутри Unity-gameplay `UniTask` почти всегда предпочтительнее.

---

## Часть 4. Когда что выбирать

### IEnumerator (корутины)
- Проект **без UniTask**, и нужна простая привязанная к объекту последовательность по времени.
- Чисто Unity-визуальные тайминги, где не важны возврат значения и обработка ошибок.
- Legacy-код, который уже на корутинах.

> При наличии UniTask новые корутины писать смысла мало — UniTask их полностью покрывает и на типичных путях не аллоцирует.

### Task
- **IO-bound** работа и интеграция с **.NET-библиотеками**, которые возвращают `Task` (HTTP-клиенты, БД, gRPC).
- **CPU-bound** работа, которую нужно увести в **пул потоков** (`Task.Run`) — тяжёлые вычисления вне главного потока.
- Код, **переиспользуемый вне Unity** (общий Domain-слой, серверная часть).
- Когда результат нужно `await` **несколько раз** (Task это позволяет, UniTask — нет без `Preserve`).

> Важно: после `Task.Run` вы **в другом потоке** — перед обращением к Unity API вернитесь в главный (`await UniTask.SwitchToMainThread()` или через SynchronizationContext).

### UniTask
- **Дефолт для async в Unity-gameplay/UI**.
- Ожидание **кадров и таймингов** (`Yield`, `DelayFrame`, `WaitUntil`).
- Ожидание **Unity-операций**: Addressables, `SceneManager.LoadSceneAsync`, `UnityWebRequest`, `DOTween` через `.ToUniTask()`.
- **Горячие пути**, где важна нулевая аллокация и нагрузка на GC.
- Когда нужна аккуратная **отмена по жизни объекта** (`GetCancellationTokenOnDestroy`).

```csharp
// CPU-работа в пуле потоков, затем возврат в главный поток для Unity API
async UniTask ProcessAsync(CancellationToken ct)
{
    await UniTask.SwitchToThreadPool();          // ушли в фоновый поток
    var result = HeavyCompute();                 // тяжёлый расчёт, главный поток свободен
    await UniTask.SwitchToMainThread(ct);        // вернулись — теперь можно Unity API
    transform.position = result;                 // безопасно: мы в главном потоке
}
```

---

## Senior-нюансы и подводные камни

- **`async void` — почти всегда ошибка.** Вызывающий код не может его `await`, отменить и перехватить его исключение: исключение публикуется в `SynchronizationContext` — в Unity (`UnitySynchronizationContext`) оно логируется, в .NET-процессе без контекста завершает процесс. Допустим только в обработчиках событий. В UniTask-мире вместо него — `UniTaskVoid` + `.Forget()` для fire-and-forget.
- **Корутина не передаёт исключение вызывающему коду, async — передаёт.** Исключение в корутине логируется и завершает её, но запустивший код об ошибке не узнаёт; в `async`-методе исключение всплывает в `await` и перехватывается `try/catch`. Это весомый аргумент за async для логики, где важна обработка ошибок.
- **Отмена обязательна, а не опциональна.** Прокидывайте `CancellationToken` во все async-методы и привязывайте к жизни объекта (`this.GetCancellationTokenOnDestroy()`), иначе UniTask продолжит выполняться после уничтожения объекта (в отличие от корутины, которая останавливается при деактивации GameObject). Отмена бросает `OperationCanceledException` — это штатный поток, а не ошибка.
- **UniTask нельзя await дважды.** Это struct, «потребляется» одним await. Для разделяемого результата — `.Preserve()` или `AsyncLazy<T>`.
- **`UniTask.Delay` по умолчанию масштабируется `Time.timeScale`.** На паузе (`timeScale = 0`) задержка не идёт. Нужен независимый таймер — `DelayType.UnscaledDeltaTime` или `Realtime`.
- **`ConfigureAwait(false)` теряет главный поток.** В Unity это обычно не нужно и опасно: продолжение может оказаться не в главном потоке. Для UniTask вопрос неактуален — оно само про PlayerLoop.
- **Не трогать Unity API из пула потоков.** После `Task.Run`/`SwitchToThreadPool` любой доступ к `GameObject`/`Transform`/компонентам — только после возврата в главный поток.
- **`WhenAll` для параллельного ожидания.** Несколько независимых загрузок запускают разом и ждут вместе: `await UniTask.WhenAll(a, b, c)` — быстрее, чем последовательные await.

---

## Вопросы для самопроверки

1. **Асинхронность и многопоточность — это одно и то же?** (Нет: async — ожидание без блокировки, может быть однопоточным; многопоточность — параллельное исполнение.)
2. **Во что компилятор разворачивает `async/await`?** (В конечный автомат с continuation на каждом `await`.)
3. **Почему `Task` создаёт нагрузку на GC, а `UniTask` — нет?** (`Task` — class в куче + бокс state machine; `UniTask` — struct, а state machine и источники результата переиспользуются из пула.)
4. **Как ведут себя исключения в корутине и в `async`?** (Корутина логирует исключение и завершается, вызывающий код его не получает; в async исключение всплывает на `await`.)
5. **Можно ли `await` один `UniTask` дважды? Что делать, если надо?** (Нельзя — struct потребляется; `.Preserve()` / `AsyncLazy`.)
6. **Куда вернётся код после `await` в Unity и кто это решает?** (В главный поток через `UnitySynchronizationContext`; `ConfigureAwait(false)` это ломает.)
7. **Чем опасен `async void`?** (Нельзя await, отменить и перехватить исключение: оно уходит в `SynchronizationContext` — в Unity логируется, без контекста завершает процесс; вместо — `UniTaskVoid` + `.Forget()`.)
8. **Корутина останавливается при деактивации GameObject. А UniTask?** (Нет — продолжится, пока не отменишь токеном; нужна привязка `GetCancellationTokenOnDestroy`.)
9. **Сделал тяжёлый расчёт в `Task.Run`, упал на обращении к `transform`. Почему?** (Код в пуле потоков; Unity API не потокобезопасен — вернуться в главный поток.)
10. **Когда `Task` уместнее `UniTask`?** (IO/CPU в пуле потоков, .NET-библиотеки, код вне Unity, многократный await.)

---
