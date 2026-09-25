[← К содержанию](../README.md)

# Современный C#: record, pattern matching, switch expressions

> Unity 2021.2 и новее (включая Unity 6) официально поддерживает C# 9; возможности C# 10+ (`record struct`, `global using` и др.) официально не поддерживаются. Для `record` и `init`-сеттеров нужен тип `System.Runtime.CompilerServices.IsExternalInit`, которого нет в BCL Unity: его объявляют в проекте вручную. Сериализатор Unity `record` не поддерживает. Точный список — в разделе Manual «C# compiler» для своей версии редактора.

## record

`record` — ссылочный тип с автоматическим **значимым равенством** и неизменяемостью «из коробки».

```csharp
public record PlayerStats(int Health, int Mana);
```

Компилятор генерирует:
- конструктор и init-only свойства из позиционных параметров;
- `Equals`/`GetHashCode` по значению (сравнивают все поля);
- `ToString` с выводом полей;
- деконструктор;
- `with`-выражение для создания изменённой копии:

```csharp
var s2 = stats with { Health = 100 };   // копия с одним изменённым полем
```

`record struct` (C# 10) — значимый тип с тем же синтаксисом; в Unity недоступен (C# 9). `record` применять для иммутабельных DTO/конфигов; для часто меняющихся игровых данных каждого кадра — осторожно (`with` на `record class` аллоцирует копию).

## Pattern matching

Сопоставление по форме и типу значения:

```csharp
// type pattern
if (obj is Enemy e) e.TakeDamage(10);

// property pattern
if (hit is { distance: < 5f, collider: not null }) { … }

// relational + logical patterns
string Grade(int x) => x switch
{
    >= 90 => "A",
    >= 75 and < 90 => "B",
    < 0 => throw new ArgumentOutOfRangeException(),
    _ => "C"
};
```

> **Ловушка Unity:** паттерны `is null` / `not null` проверяют ссылку и не вызывают перегруженный `==` у `UnityEngine.Object`. Уничтоженный объект (fake null, см. [equality](equality.md)) проходит проверку `not null`. Для Unity-объектов проверять через `==`/`!=` или неявное приведение к `bool` (`if (collider)`).

## switch expression

Выражение (возвращает значение), а не оператор. Компактнее классического `switch`, требует обработки всех случаев (иначе предупреждение); `_` — ветка по умолчанию.

```csharp
float Multiplier(Rarity r) => r switch
{
    Rarity.Common    => 1f,
    Rarity.Rare      => 1.5f,
    Rarity.Legendary => 3f,
    _ => throw new ArgumentOutOfRangeException(nameof(r))
};
```

Преимущества: исчерпывающность проверяется компилятором, нет проваливания (fall-through), нет забытого `break`.

## Прочее современное

- **Target-typed `new`**: `Dictionary<int, string> map = new();`
- **`nameof`**: имя символа строкой (рефакторинг-безопасно).
- **Null-операторы**: `?.`, `??`, `??=`.
- **Switch на кортежах**: `(a, b) switch { … }`.

## Что спрашивают на собеседовании

- Чем `record` отличается от `class` (значимое равенство, иммутабельность, `with`).
- Что делает `with`-выражение.
- Преимущества switch expression над классическим switch.
- Виды паттернов (type, property, relational, logical).

---