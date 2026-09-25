[← К содержанию](../README.md)

# Orchestrator (координатор use-case)

Оркестратор — класс слоя Application (см. [Clean Architecture](../02-architecture/clean-architecture.md)), который координирует **один сценарий использования**, дёргая несколько сервисов в нужном порядке. Применяется, когда use-case затрагивает 3+ сервиса.

## Зачем

Альтернатива «менеджеру на 500 строк» и логике, размазанной по `MonoBehaviour`. Каждый сценарий («начать уровень», «купить предмет», «завершить матч») — свой небольшой оркестратор. Это [SRP](../02-architecture/solid.md): один класс — одна причина для изменения.

## Форма

```csharp
public sealed class StartLevelOrchestrator
{
    private readonly ISaveStore _save;
    private readonly ILevelLoader _loader;
    private readonly IAnalytics _analytics;

    public StartLevelOrchestrator(ISaveStore save, ILevelLoader loader, IAnalytics analytics)
    {
        _save = save; _loader = loader; _analytics = analytics;
    }

    public async UniTask Execute(int levelId, CancellationToken ct)
    {
        var progress = await _save.Load(ct);
        await _loader.Load(levelId, ct);
        _analytics.Track("level_started", levelId);
    }
}
```

Характеристики:
- Зависимости — через **конструктор** ([DI](../02-architecture/di.md)), только интерфейсы.
- **Без `UnityEngine`-вызовов** — вызывает абстракции. Поэтому юнит-тестируется со стабами в EditMode (см. [тестирование](../09-testing/testing.md)).
- **Асинхронный** (`UniTask` — дефолт) и **cancellation-aware** (принимает `CancellationToken`; см. [async](../05-async/async.md)).
- Presentation-слой (`MonoBehaviour`) получает оркестратор через DI и вызывает `Execute` из обработчика кнопки.

## Отличие от соседних понятий

- **Orchestrator vs Mediator**: оркестратор активно управляет порядком вызовов конкретного сценария; медиатор лишь развязывает участников, не владея сценарием.
- **Orchestrator vs God-object Manager**: оркестратор — на один use-case и тонкий; «менеджер» накапливает несвязанную логику (антипаттерн).

## Что спрашивают на собеседовании

- Зачем оркестратор (координация одного use-case, SRP, против god-менеджеров).
- Почему он не содержит `UnityEngine` и как это даёт тестируемость.
- Где он лежит в слоях (Application) и кто его вызывает (Presentation через DI).
- Чем отличается от Mediator.

---