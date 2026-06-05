[← К содержанию](../README.md)

# Dependency Injection (DI) и Zenject

## Часть 1. Что такое DI и зачем он нужен

**Dependency Injection (внедрение зависимостей)** — приём, при котором объект **получает** свои зависимости извне, вместо того чтобы создавать их сам (`new`) или искать (`FindObjectOfType`, синглтон, service locator).

DI — это конкретная реализация принципа **Inversion of Control (IoC)** и практическое следствие [SOLID → DIP](solid.md): класс зависит от **абстракций**, а кто подставит конкретную реализацию — решает внешний код (DI-контейнер).

```csharp
// БЕЗ DI: класс сам добывает зависимости — жёсткая связанность
public class Game
{
    private readonly SaveSystem _save = new SaveSystem();          // жёсткая зависимость, создаётся внутри
    private readonly AudioManager _audio = AudioManager.Instance;  // синглтон
}

// С DI: зависимости приходят снаружи через конструктор
public class Game
{
    private readonly ISaveSystem _save;
    private readonly IAudioService _audio;

    public Game(ISaveSystem save, IAudioService audio)   // контейнер подставит реализации
    {
        _save = save;
        _audio = audio;
    }
}
```

### Зачем это нужно (что даёт на практике)

- **Слабая связанность** — класс знает про интерфейс, а не про конкретный тип. См. [coupling/decoupling](coupling-decoupling.md).
- **Тестируемость** — в тест подставляется мок/стаб вместо реальной файловой системы или сети. Это главный практический аргумент.
- **Замена реализаций** — `IAnalytics` → Firebase в релизе и `NullAnalytics` в редакторе, без правок потребителя (OCP).
- **Явные зависимости** — по сигнатуре конструктора сразу видно, что классу реально нужно. Если в конструкторе 8 параметров — это запах: класс делает слишком много (нарушение SRP), и DI делает проблему **видимой**, а не прячет.
- **Управление временем жизни** — контейнер централизованно решает, что синглтон, что создаётся заново, что живёт в рамках сцены.

### DI ≠ DI-контейнер

DI можно делать **руками** (`Poor Man's DI` — просто прокидывать через конструкторы из `Main`/composition root). Контейнер (Zenject, VContainer) нужен, когда граф зависимостей становится большим: он автоматически разрешает дерево и управляет жизненным циклом. Контейнер — это инструмент, а не сам принцип.

### Виды внедрения

| Способ | Когда |
|---|---|
| **Constructor injection** | По умолчанию для plain C# классов. Зависимости обязательны и неизменяемы (`readonly`). |
| **Method / property injection** | Когда конструктор недоступен — например MonoBehaviour (его создаёт Unity, конструктор не вызвать). |
| **Field injection** | Самый неявный, ломает тестируемость без контейнера. На проде избегаем. |

> **Service Locator — это анти-паттерн, а не DI.** При `Locator.Get<IFoo>()` зависимость **скрыта** внутри метода: по сигнатуре класса не видно, что ему нужно, и тест нельзя сконфигурировать через конструктор. DI делает зависимости явными — в этом ключевая разница.

---

## Часть 2. Zenject (Extenject)

Решает то, чего нет в Unity из коробки: автоматическое построение графа зависимостей и управление их временем жизни, в том числе для MonoBehaviour.

### Ключевые сущности

- **DiContainer** — собственно контейнер: хранит привязки (bindings) и умеет разрешать (`Resolve`) граф.
- **Installer** — место, где регистрируются привязки. `MonoInstaller` (вешается в сцене) или `ScriptableObjectInstaller` (ассет, для проектного скоупа).
- **Context** — точка входа, которая создаёт контейнер и запускает инсталлеры:
  - **ProjectContext** — один на всё приложение (ассет в `Resources`), переживает смену сцен → проектные синглтоны.
  - **SceneContext** — свой на каждую сцену, наследует ProjectContext.
  - **GameObjectContext** — суб-контейнер на отдельном объекте (например, на каждом враге свой scope).

### Привязки (binding) — основа всего

Базовый синтаксис: `Bind<Контракт>().To<Реализация>().AsЖизнь()`.

```csharp
public class GameInstaller : MonoInstaller
{
    public override void InstallBindings()
    {
        // интерфейс → реализация, один экземпляр на контейнер
        Container.Bind<ISaveSystem>().To<FileSaveSystem>().AsSingle();

        // несколько контрактов → один экземпляр
        Container.Bind(typeof(ITickable), typeof(IInitializable))
                 .To<GameController>().AsSingle();

        // значение/конфиг из инспектора
        Container.BindInstance(_playerConfig);

        // фабрика вместо new для префабов (см. ниже)
        Container.BindFactory<Enemy, Enemy.Factory>()
                 .FromComponentInNewPrefab(_enemyPrefab);
    }
}
```

#### Scope — время жизни (частый вопрос на собесе)

| Метод | Поведение |
|---|---|
| `AsSingle()` | Один экземпляр на контейнер. Повторные резолвы возвращают тот же объект. |
| `AsTransient()` | Новый экземпляр на **каждый** запрос/инъекцию. |
| `AsCached()` | Один экземпляр на **эту** привязку (важно, когда один тип привязан несколько раз с разными условиями). |

> Нюанс: `AsSingle()` дважды для одного и того же контракта → исключение. Если нужно несколько реализаций одного интерфейса — `AsCached()` + условные привязки (`WhenInjectedInto<T>`), либо резолв списком `List<IFoo>`.

#### Источники объекта — `FromX`

Куда контейнер берёт экземпляр: `FromNew()` (по умолчанию), `FromInstance(obj)`, `FromComponentInHierarchy()`, `FromComponentInNewPrefab(prefab)`, `FromMethod(ctx => ...)`, `FromResolve()`, `FromSubContainerResolve()`. Это отвечает на вопрос «уже существующий объект или создать новый, и как именно».

### Инъекция в MonoBehaviour

У MonoBehaviour **нельзя вызвать конструктор** (его инстанцирует Unity), поэтому Zenject внедряет через `[Inject]`-метод. На проде — именно метод/конструктор, **не** field injection.

```csharp
public class Player : MonoBehaviour
{
    private ISaveSystem _save;
    private PlayerConfig _config;

    [Inject]                                   // вызывается контейнером после Awake, до Start
    public void Construct(ISaveSystem save, PlayerConfig config)
    {
        _save = save;
        _config = config;
    }
}
```

Чтобы Zenject знал про объект на сцене, его регистрируют (`Bind<Player>().FromComponentInHierarchy().AsSingle()`) или создают через фабрику/`InstantiatePrefab`. Объекты, заспавненные через `GameObject.Instantiate`, инъекцию **не получат** — для рантайм-спавна используют `Container.InstantiatePrefab` или фабрику.

### Lifecycle-интерфейсы — замена Update/Awake без MonoBehaviour

Главная сила Zenject: **plain C# классы получают жизненный цикл**, оставаясь чистыми и тестируемыми (см. слой Application в архитектуре).

| Интерфейс | Аналог в Unity |
|---|---|
| `IInitializable.Initialize()` | `Start` (после построения графа) |
| `ITickable.Tick()` | `Update` |
| `IFixedTickable.FixedTick()` | `FixedUpdate` |
| `ILateTickable.LateTick()` | `LateUpdate` |
| `IDisposable.Dispose()` | `OnDestroy` (при разрушении контекста) |

```csharp
// бизнес-логика без UnityEngine — юнит-тестируется без Play Mode
public class ScoreController : IInitializable, ITickable, IDisposable
{
    private readonly IScoreView _view;
    public ScoreController(IScoreView view) => _view = view;   // constructor injection

    public void Initialize() { /* стартовая настройка */ }
    public void Tick() { /* вызывается каждый кадр контейнером */ }
    public void Dispose() { /* очистка при закрытии скоупа */ }
}

// в инсталлере:
Container.BindInterfaces.To<ScoreController>().AsSingle();   // привязать сразу по всем интерфейсам
```

> Порядок `Tick()` детерминирован и настраивается через `BindTickableExecutionOrder` — в отличие от недетерминированного порядка `Update` между обычными MonoBehaviour.

### Фабрики — создание объектов в рантайме

`new` на префабе ломает DI (новый объект не получит зависимости). Решение — `PlaceholderFactory`: фабрика тоже инъецируется, а созданные ею объекты проходят полную инъекцию.

```csharp
public class Enemy : MonoBehaviour
{
    [Inject] public void Construct(IPathfinding pathfinding) { /* ... */ }

    public class Factory : PlaceholderFactory<Enemy> { }   // Zenject сгенерирует реализацию
}

// привязка:
Container.BindFactory<Enemy, Enemy.Factory>().FromComponentInNewPrefab(_enemyPrefab);

// использование — спавнер получает фабрику, а не префаб и не new:
public class Spawner : ITickable
{
    private readonly Enemy.Factory _factory;
    public Spawner(Enemy.Factory factory) => _factory = factory;
    public void Tick() { var e = _factory.Create(); /* e уже с внедрёнными зависимостями */ }
}
```

### SignalBus — события без жёстких ссылок

Zenject-шина событий. Замена `static event` и прямых ссылок: издатель и подписчик не знают друг о друге (Observer/Mediator на уровне контейнера).

```csharp
public struct PlayerDiedSignal { public int Score; }

// в инсталлере:
Container.DeclareSignal<PlayerDiedSignal>();

// издатель:
_signalBus.Fire(new PlayerDiedSignal { Score = 100 });

// подписчик (не забыть отписку в Dispose):
_signalBus.Subscribe<PlayerDiedSignal>(OnPlayerDied);
```

### MemoryPool — пулинг через контейнер

Пул объектов как привязка — снижает нагрузку на [GC](../03-unity-core/unity-gc.md), сохраняя инъекцию.

```csharp
public class Bullet : MonoBehaviour { public class Pool : MemoryPool<Bullet> { } }

Container.BindMemoryPool<Bullet, Bullet.Pool>()
         .WithInitialSize(50)
         .FromComponentInNewPrefab(_bulletPrefab);
// _pool.Spawn() / _pool.Despawn(bullet) вместо Instantiate/Destroy
```

---

## Разбор частых проблем

### 1. Когда граф не резолвится

Zenject строит граф при создании контейнера (вход в Play Mode / загрузка сцены) и падает с `ZenjectException`, если не может его собрать. Типичные причины:

- **Нет привязки** — `Unable to resolve type 'IFoo'`. Забыли `Bind`, забыли добавить инсталлер в список **Mono Installers** у `SceneContext`/`ProjectContext`, или привязка ушла не в тот скоуп. Самая частая причина.
- **Несколько привязок одного контракта** — `Found multiple matches when only one was expected`. Один интерфейс привязан дважды без условий, а резолвится как одиночный. Решение: резолвить списком `List<IFoo>`, либо разделить через `WhenInjectedInto<T>` / `AsCached` с условием.
- **Циклическая зависимость через конструктор** — `Circular dependency detected`. См. пункт 3 ниже.
- **Объект создан мимо контейнера** — заспавнили через `GameObject.Instantiate` или `new` → `[Inject]` не вызывается, поля остаются `null` (это уже не `ZenjectException`, а `NullReference` в рантайме). Нужно `Container.InstantiatePrefab` / фабрика.
- **MonoBehaviour не виден контейнеру** — объект не в иерархии `SceneContext` и не зарегистрирован (`FromComponentInHierarchy`), поэтому его `[Inject]`-метод не вызовется.
- **Резолв до построения графа** — обращение к зависимости в `Awake`/конструкторе MonoBehaviour раньше, чем отработал `[Inject]`-метод (инъекция идёт после `Awake`, до `Start`).

```csharp
// если зависимость опциональна — иначе отсутствие привязки = исключение
[Inject] public void Construct([InjectOptional] IAnalytics analytics = null) { }
```

> **Инструмент:** Zenject умеет **валидировать граф без запуска игры** — `Validate` (галка в `SceneContext` / меню Zenject → Validate Current Scene). Ловит отсутствующие/двойные привязки и циклы на этапе входа в Play Mode, а не в рантайме на проде.

### 2. Как ускорить долгий прогрев контейнера

Долгий старт — это почти всегда **не** сам резолв, а одно из двух: тяжёлая работа при создании объектов или рантайм-рефлексия на большом графе. Лечится по слоям:

- **Сначала профилировать.** Открыть Profiler на загрузке сцены и понять, где время: в конструкторах/`Initialize` (логика) или в самом построении графа (рефлексия). Лечение разное.
- **Конструкторы должны быть минимальными.** Конструктор только присваивает ссылки — никаких загрузок ассетов, парсинга JSON, сетевых вызовов. Тяжёлое выносим в `IInitializable.Initialize()` (а лучше — в `async`/UniTask) и растягиваем по кадрам, чтобы не морозить главный поток.
- **Ленивость вместо `NonLazy`.** `AsSingle` по умолчанию **ленив** — объект создаётся при первом резолве. `NonLazy()` форсирует создание на старте; уберите лишние `NonLazy`, оставив их только там, где объект обязан жить с самого начала (например, `ITickable`-сервисы).
- **`Lazy<T>` / фабрики для дорогих узлов.** Если зависимость дорогая, но нужна не сразу — инъецировать `Lazy<IHeavy>` или фабрику, тогда создание откладывается до первого обращения и не попадает в прогрев.
- **Zenject Reflection Baking.** На больших графах (и особенно под IL2CPP/AOT) рантайм-рефлексия — основной источник задержки. Включите **Reflection Baking** (генерация кода вместо рефлексии в рантайме) — граф собирается заметно быстрее.
- **Дробить скоупы.** Не складывать всё в один `ProjectContext`/`SceneContext` — тогда весь граф грузится на старте. Часть сервисов выносить в `GameObjectContext` / отдельные сцены и поднимать лениво, когда нужный экран реально открывается.
- **Крайняя мера — сменить контейнер.** Если рефлексия Zenject стала бутылочным горлышком, **VContainer** (source-gen, без рантайм-рефлексии) прогревается быстрее. Это архитектурное решение, а не локальная правка.

### 3. Перекрёстные (циклические) зависимости: A требует B, B требует A

**Сначала — это запах дизайна.** Цикл почти всегда означает, что ответственности размазаны между двумя классами. Правильно — убрать сам цикл, а не обходить его технически:

- **Выделить третий класс / общую зависимость C**, от которой зависят оба (Mediator/посредник) — связь A↔B превращается в A→C←B.
- **Развернуть одну сторону на событие** — вместо того чтобы B держал ссылку на A, A подписывается на сигнал B (`SignalBus`). Прямая ссылка исчезает.

Если разрыв по дизайну невозможен прямо сейчас, технические способы (Zenject **бросит исключение** на циклическую зависимость через конструктор, поэтому одну сторону нужно вынести из конструктора):

- **Method/property injection** для одной из сторон. К моменту вызова `[Inject]`-метода объект уже создан, поэтому цикл «создания» разрывается:

```csharp
public class A { public A(B b) { } }              // A создаётся первым, требует B
public class B
{
    private A _a;
    [Inject] public void Construct(A a) => _a = a; // B создаётся без A, A внедряется позже
}
```

- **`Lazy<T>` / фабрика** — отложить получение второй зависимости до первого обращения:

```csharp
public class A { public A(Lazy<B> b) { } }   // B не создаётся в момент конструирования A
```

> На собесе ценится именно такой порядок ответа: **сначала** «это сигнал к рефакторингу — выделить посредника/событие», и **только потом** «технически Zenject разрывает цикл через method-injection или `Lazy<T>`». Кандидат, который сразу берёт `Lazy<T>`, борется со следствием, а не с причиной.

---

## Вопросы для самопроверки

Проверь себя — на senior-собесе про DI спрашивают не определения, а понимание следствий:

1. **Чем DI отличается от Service Locator, если оба «дают зависимости»?** (DI делает зависимости явными в сигнатуре; Locator прячет их внутри метода → ломает тестируемость и читаемость.)
2. **Почему в MonoBehaviour нельзя constructor injection и что используется вместо?** (Unity сама создаёт компонент через свой аллокатор, конструктор не вызвать → `[Inject]`-метод после `Awake`.)
3. **`AsSingle` vs `AsCached` vs `AsTransient` — в чём разница и когда `AsSingle` бросит исключение?** (Повторная привязка того же контракта.)
4. **Объект заспавнили через `Instantiate` и его зависимости `null`. Почему и как чинить?** (Прошёл мимо контейнера → `InstantiatePrefab`/фабрика.)
5. **Ленивы ли `AsSingle`-объекты? Что меняет `NonLazy()`?** (Ленивы по умолчанию; `NonLazy` создаёт на старте.)
6. **Что произойдёт при циклической зависимости через конструктор и как её правильно решать?** (Исключение; сначала рефакторинг через посредника/событие, потом — method-injection/`Lazy<T>`.)
7. **Зачем инъецировать `IEnumerable<IHandler>` вместо конкретных хендлеров?** (Open/Closed: добавление обработчика = новая привязка, потребитель не меняется.)
8. **Почему `[Inject] DiContainer` в обычном классе — анти-паттерн?** (Это скрытый Service Locator — зависимости снова прячутся.)
9. **DI «замедляет старт». За счёт чего и что с этим делать?** (Рефлексия + тяжёлые конструкторы; Reflection Baking, ленивость, дробление скоупов.)
10. **Чем оправдан DI-контейнер против ручного прокидывания зависимостей?** (Автоматический резолв дерева и управление lifetime; на маленьком графе ручной DI проще.)

---

## Senior-нюансы (что отличает на собесе)

- **Composition root один.** Вся проводка зависимостей — в инсталлерах (`ProjectContext`/`SceneContext`), а не размазана по коду. Классы не лезут в `Container` сами.
- **Не инъецировать контейнер.** `[Inject] DiContainer` в обычном классе превращает DI обратно в Service Locator — анти-паттерн. Контейнер уместен только в инфраструктуре (фабрики, инсталлеры).
- **Стоимость.** Резолв использует рефлексию, но Zenject **кэширует** её при старте. Дорог именно прогрев контейнера (загрузка сцены), а не резолвы в рантайме. Тяжёлый спавн в кадре всё равно идёт через пулы/фабрики, а не `Resolve` на горячем пути.
- **`AsSingle` vs `AsCached`** — классический вопрос: `AsSingle` запрещает повторную привязку контракта, `AsCached` — нет. Понимание этого = понимание устройства скоупов.
- **Скоупы и память.** Объекты `SceneContext` живут до выгрузки сцены и получают `Dispose()`; `ProjectContext` — на всё приложение. Неправильный скоуп → либо утечка, либо преждевременное разрушение.
- **Zenject vs VContainer.** VContainer быстрее и легче (меньше рефлексии, source-gen), API похож (`LifetimeScope`, `IContainerBuilder`). В этом проекте по умолчанию — **Zenject**; не смешивать два контейнера в одной сборке.
- **DI не отменяет архитектуру.** Контейнер лишь проводит зависимости. Если логика навалена в один «менеджер» — DI это не лечит, лечит разделение на слои (Domain/Application/Presentation) и SRP.

---
