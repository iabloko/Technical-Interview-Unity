[← К содержанию](../README.md)

# VContainer (и сравнение с Zenject)

VContainer — лёгкий DI-контейнер для Unity, альтернатива [Zenject](di.md). Общая идея DI та же (см. [di.md](di.md)); отличаются API и характеристики.

## Ключевые сущности

| Zenject | VContainer | Роль |
|---|---|---|
| `DiContainer` | `IObjectResolver` | контейнер, резолвит зависимости |
| `MonoInstaller` / `Installer` | `LifetimeScope` | точка регистрации |
| `Container.Bind<T>()` | `builder.Register<T>()` | привязка |
| `[Inject]` | `[Inject]` | пометка для внедрения |
| `SignalBus` | MessagePipe (`IPublisher`/`ISubscriber`) | события |

## Регистрация

```csharp
public class GameLifetimeScope : LifetimeScope
{
    protected override void Configure(IContainerBuilder builder)
    {
        builder.Register<IScoreService, ScoreService>(Lifetime.Singleton);
        builder.RegisterComponentInHierarchy<Player>();          // существующий объект сцены
        builder.RegisterEntryPoint<GameController>();             // аналог lifecycle-интерфейсов
    }
}
```

- `Lifetime`: `Singleton` / `Scoped` / `Transient`.
- Предпочтительно **constructor injection** для чистых C#-классов; для сценовых `MonoBehaviour` — `RegisterComponentInHierarchy` / `RegisterComponentInNewPrefab`.
- Точки входа (`IStartable`, `ITickable`) через `RegisterEntryPoint` — замена `Update`/`Start` без `MonoBehaviour` (аналог Zenject lifecycle-интерфейсов).

## VContainer vs Zenject

| | Zenject | VContainer |
|---|---|---|
| Зрелость/экосистема | большая, давно на рынке | новее, активно растёт |
| Производительность резолва | медленнее, больше аллокаций | быстрее, меньше GC, есть codegen под IL2CPP |
| Прогрев контейнера | заметный на больших графах | быстрее |
| API | богатый, местами тяжеловесный | минималистичный |
| События | встроенный `SignalBus` | через MessagePipe (отдельный пакет) |

## Правило выбора (важно для собеседования)

- Определять контейнер **по проекту**: что уже подключено в `manifest.json` (`com.svermeulen.extenject` vs `jp.hadashikick.vcontainer`). Не смешивать оба в одной сборке.
- Нет ни одного — это решение команды, не изобретать третий и не катить самодельный Service Locator (см. [паттерны](../08-patterns/design-patterns.md)).
- VContainer выбирают, когда важны производительность/аллокации DI и мобильные цели; Zenject — за зрелость, `SignalBus` и привычность.

## Что спрашивают на собеседовании

- Чем VContainer отличается от Zenject (производительность, аллокации, минимализм API).
- Что такое `LifetimeScope` и виды `Lifetime`.
- Почему предпочтителен constructor injection.
- Почему нельзя мешать два контейнера и как выбрать.

---