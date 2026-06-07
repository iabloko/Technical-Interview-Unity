[← К содержанию](../README.md)

# Современный C#: record, pattern matching, switch expressions

> Версия языка в Unity зависит от рантайма. Unity 2021+ (.NET Standard 2.1) поддерживает C# 9; часть возможностей C# 10+ доступна частично. Проверять под конкретную версию редактора.

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

`record struct` (C# 10) — значимый тип с тем же синтаксисом. Применять для иммутабельных DTO/конфигов; для часто меняющихся игровых данных каждого кадра — осторожно (создание копий через `with` аллоцирует для `record class`).

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