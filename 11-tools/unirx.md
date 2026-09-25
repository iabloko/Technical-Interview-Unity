[← К содержанию](../README.md)

# UniRx / R3 (реактивное программирование)

UniRx — реализация Reactive Extensions (Rx) для Unity; **R3** — её современный преемник. Опциональная библиотека: применять, **только если проект уже от неё зависит** (проверить `manifest.json`); иначе предпочесть обычные [события](../01-csharp/delegates-events.md)/[UniTask](../05-async/async.md).

## Идея

Данные как **поток событий** (`IObservable<T>`), на который подписываются и который преобразуют операторами (`Where`, `Select`, `Throttle`, `CombineLatest`). Удобно для связывания модель→представление и обработки потоков ввода.

## Ключевые сущности

| Сущность | Назначение |
|---|---|
| `IObservable<T>` | источник потока значений |
| `Subject<T>` | и источник, и приёмник (можно `OnNext`) |
| `ReactiveProperty<T>` | наблюдаемое значение; уведомляет при изменении |
| ObservableTriggers | события `MonoBehaviour` (`OnCollisionEnterAsObservable`) как потоки |

## ReactiveProperty — связывание модель→view

```csharp
// Model
public readonly ReactiveProperty<int> Score = new(0);

// View
_model.Score
    .Subscribe(v => _label.SetText(v.ToString()))
    .AddTo(this);     // отписка при уничтожении
```

Это основа [MVVM](../08-patterns/mvp-mvvm.md): View декларативно подписана на свойство ViewModel и обновляется автоматически.

## Операторы для потоков ввода

```csharp
this.UpdateAsObservable()
    .Where(_ => Input.GetMouseButtonDown(0))
    .ThrottleFirst(TimeSpan.FromSeconds(0.5))   // антиспам кликов
    .Subscribe(_ => Fire())
    .AddTo(this);
```

Типичное: `Throttle`/`Debounce` (поле поиска), `ThrottleFirst` (кулдаун), `CombineLatest` (форма «готова, когда все поля валидны»), `DistinctUntilChanged`.

## Управление временем жизни (важно)

Подписка возвращает `IDisposable`. Не освобождённая подписка — **утечка** (как и у [событий](../01-csharp/delegates-events.md)):
- `.AddTo(this)` / `.AddTo(disposables)` — отписка при уничтожении `MonoBehaviour`/`CompositeDisposable`.
- Без `AddTo`/`Dispose` подписка живёт и держит ссылки.

## UniRx vs UniTask vs C# events

- Разовое асинхронное действие → [UniTask](../05-async/async.md).
- Простое уведомление 1→N → C# `event`/`Action`.
- **Поток** событий с преобразованиями (throttle/combine/реактивное связывание) → UniRx/R3.

Не тащить Rx ради одного колбэка — это усложнение (см. [KISS](../02-architecture/best-practices.md)).

## Что спрашивают на собеседовании

- Что такое `IObservable`/`ReactiveProperty` и где это уместно (реактивное связывание, потоки ввода).
- Как UniRx реализует MVVM-биндинг.
- Как управлять временем жизни подписки (`AddTo`/`Dispose`), чем грозит пропуск.
- Когда Rx, а когда хватит event/UniTask.

---