[← К содержанию](../README.md)

# Тестирование в Unity (Unity Test Framework)

Unity Test Framework (UTF) — официальный инструмент тестирования поверх **NUnit**. Делит тесты на два режима.

## EditMode vs PlayMode

| | EditMode | PlayMode |
|---|---|---|
| Где выполняется | в редакторе, без запуска игры | в работающем плеере/сцене |
| Игровой цикл | нет (`Update` не идёт) | есть, кадры тикают |
| Скорость | быстрые | медленнее |
| Для чего | чистая логика, классы, редакторные инструменты | поведение в рантайме, физика, корутины, lifecycle |
| Ожидание | `[UnityTest]` + `yield return null` (тики редактора) | `[UnityTest]` + `yield` (кадры, `WaitForSeconds`) |

```csharp
[Test]                       // EditMode: чистая логика
public void Damage_Reduces_Health()
{
    var h = new Health(100);
    h.Apply(30);
    Assert.AreEqual(70, h.Current);
}

[UnityTest]                  // PlayMode: ждём кадры
public IEnumerator Projectile_Moves_Forward()
{
    var p = Object.Instantiate(_prefab);
    var start = p.transform.position;
    yield return new WaitForSeconds(0.5f);
    Assert.Greater(p.transform.position.z, start.z);
}
```

С Unity Test Framework 1.3 тест может быть `async Task`-методом с атрибутом `[Test]`: фреймворк проверяет завершение задачи на каждом update.

## Тестопригодная архитектура (главное)

Тестируется то, что отвязано от движка. Поэтому тесты — аргумент за всё остальное в этой базе:

- Бизнес-логику держать в **обычных C#-классах**, не в `MonoBehaviour` (см. [MVP/MVVM](../08-patterns/mvp-mvvm.md), [DI](../02-architecture/di.md)). Их можно тестировать в быстром EditMode без сцены.
- Зависимости — через интерфейсы ([DIP](../02-architecture/solid.md)), чтобы подменять моками.
- `MonoBehaviour`, обращающийся к статике/синглтоны/`Find`, почти нетестируем.

## Моки и тестовые дублёры

NUnit сам моков не даёт. Подходы:
- Ручные fake-реализации интерфейсов (часто достаточно).
- Библиотеки (NSubstitute/Moq) — работают в редакторе (Mono); прокси они генерируют через `Reflection.Emit`, поэтому в PlayMode-тестах на IL2CPP-билде не работают.

## Организация

- Тесты — в отдельной сборке с [asmdef](../03-unity-core/assembly-definitions.md), ссылающейся на `UnityEngine.TestRunner` и тестируемые сборки; так тесты не попадают в релизный билд.
- `[SetUp]`/`[TearDown]` — подготовка/очистка перед каждым тестом; `[OneTimeSetUp]` — раз на класс.
- Запуск: `Window → General → Test Runner`; в CI — через `-runTests` в batch mode.

## Прочие виды

- **Параметризованные**: `[TestCase(1, 2, 3)]`.
- **Performance Testing** (пакет) — замер таймингов/аллокаций как тест.
- Пирамида: много быстрых EditMode-юнит-тестов, меньше PlayMode-интеграционных.

## Что спрашивают на собеседовании

- Разница EditMode и PlayMode и когда какой.
- Почему логику выносят из `MonoBehaviour` (тестируемость).
- Как тестировать код с зависимостями (интерфейсы + моки, DI).
- Зачем `[UnityTest]` и `yield` (ожидание кадров).
- Как тесты изолируют от релизного билда (отдельный asmdef).

---