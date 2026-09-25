[← К содержанию](../README.md)

# Конвенции C# / Unity и best practices MonoBehaviour

Свод правил, которые senior применяет рефлекторно. Многие пересекаются с [производительностью](../06-performance/profiling-methodology.md) и [архитектурой](../02-architecture/clean-architecture.md).

## Именование

| Сущность | Стиль | Пример |
|---|---|---|
| Типы, методы, свойства | `PascalCase` | `PlayerController`, `TakeDamage` |
| Приватные поля | `_camelCase` | `_health`, `_isReady` |
| Сериализуемые приватные | `[SerializeField] private _camelCase` | `[SerializeField] private float _speed;` |
| Константы | `PascalCase` (не `SCREAMING_CASE`) | `MaxHealth` |
| Bool | префикс `is/has/can/should` | `_isDead`, `HasTarget` |
| async-методы (`Task`/`UniTask`) | суффикс `Async` | `LoadAsync` |

## Сериализация полей

- **`[SerializeField] private`, а не `public`** — не делать поле публичным только ради Inspector (нарушение инкапсуляции). Для неизменяемой публичной поверхности — `[field: SerializeField] public T Prop { get; private set; }`.
- Подробности — [сериализация](serialization.md).

## MonoBehaviour: best practices

- **Кешировать ссылки в `Awake`/`OnEnable`**, никогда не звать `GetComponent` в `Update`.
- **`[RequireComponent(typeof(T))]`** делает зависимость явной: редактор добавляет компонент `T` вместе с этим и не даёт его удалить. Ссылку на `T` всё равно получают через `GetComponent` в `Awake` или сериализованное поле.
- **Подписки на события — в `OnEnable`, отписка — в `OnDisable`** (корректно работают с пулингом и domain reload; см. [pooling](object-pooling.md), [события](../01-csharp/delegates-events.md)).
- **Никакой логики в конструкторе** `MonoBehaviour` — движок может ещё не инициализировать объект; использовать `Awake`.
- **Избегать `FindObjectOfType`/`GameObject.Find`/`SendMessage`** в шиппинг-коде — медленно и хрупко; внедрять через [DI](../02-architecture/di.md) или `[SerializeField]`.
- **`Update`/`FixedUpdate`/`LateUpdate` — тонкие диспетчеры**: логику выносить в чистые C#-классы, тестируемые без сцены.
- **Пустой `Update` тоже стоит дорого** — Unity всё равно его диспетчеризует. Нет логики — удалить метод. Много тикающих объектов → один `UpdateManager`, тикающий список `IUpdatable`.
- `CompareTag("Enemy")` вместо `tag == "Enemy"` (геттер `tag` при каждом обращении создаёт новую managed-строку из нативных данных).
- `Camera.main` кешировать локально (в современных версиях кешируется движком, но обращение всё равно не бесплатно).

## Конфигурация

Настраиваемые значения — в [`ScriptableObject`](scriptable-object.md), а не хардкодом в `MonoBehaviour`.

## Асинхронность, текст, твины

- **UniTask** — дефолт вместо корутин/`Task` для работы на Unity-потоке; всегда принимать `CancellationToken`, привязывать к `destroyCancellationToken` (см. [async](../05-async/async.md)). Не использовать `.GetAwaiter().GetResult()` / `.Wait()` — дедлок под sync-контекстом Unity.
- **TextMeshPro** (`TMP_Text`) вместо `UnityEngine.UI.Text`; обновлять через `SetText` (см. [строки](../01-csharp/strings.md)).
- **DOTween** вместо самописных корутин-лерпов; убивать твики на уничтожении (`SetLink`/`Kill`) — см. [dotween](../11-tools/dotween.md).

## Логирование

`Debug.Log*` — только для разработки, никогда в `Update` без гейта. В продакшене — через проектную абстракцию `ILogger`, чтобы глушить в релизе.

## Что спрашивают на собеседовании

- Почему `[SerializeField] private`, а не `public`.
- Почему не звать `GetComponent`/`Find` в `Update` и где кешировать.
- Почему подписки в `OnEnable`/`OnDisable`, а не в `Awake`/`Start`.
- Почему пустой `Update` нежелателен.
- `CompareTag` vs `==`.

---