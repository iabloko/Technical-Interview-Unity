[← К содержанию](../README.md)

# SOLID

Пять принципов проектирования (Роберт Мартин), которые помогают писать поддерживаемый и расширяемый код.

| | Принцип | Суть в одной фразе |
|---|---|---|
| **S** | Single Responsibility | Один класс — одна причина для изменения |
| **O** | Open/Closed | Открыт для расширения, закрыт для модификации |
| **L** | Liskov Substitution | Наследник заменяет базовый тип без сюрпризов |
| **I** | Interface Segregation | Много узких интерфейсов лучше одного «толстого» |
| **D** | Dependency Inversion | Зависим от абстракций, а не от реализаций |

---

## S — Single Responsibility Principle (SRP)

> У класса должна быть **только одна причина для изменения**.

Если класс отвечает и за логику игрока, и за сохранение, и за UI — изменение любого из трёх ломает остальные.

```csharp
// плохо: класс делает всё сразу
public class Player : MonoBehaviour
{
    public void TakeDamage(int dmg) { /* логика */ }
    public void SaveToDisk()        { /* работа с файлами */ }
    public void UpdateHealthBar()   { /* работа с UI */ }
}

// хорошо: ответственности разделены
public class PlayerHealth : MonoBehaviour   { public void TakeDamage(int dmg) { } }
public class SaveSystem                     { public void Save(PlayerData d) { } }
public class HealthBarView : MonoBehaviour  { public void Render(int hp) { } }
```

---

## O — Open/Closed Principle (OCP)

> Сущности **открыты для расширения, но закрыты для модификации**.

Добавление нового поведения не должно требовать правок в существующем, протестированном коде. Достигается через абстракции и полиморфизм.

```csharp
// плохо: новый тип урона = правка switch
public float Calc(DamageType type, float baseDmg) => type switch
{
    DamageType.Fire => baseDmg * 1.5f,
    DamageType.Ice  => baseDmg * 0.8f,
    _               => baseDmg,
};

// хорошо: новый тип = новый класс, старый код не трогаем
public interface IDamageModifier { float Modify(float baseDmg); }

public class FireModifier : IDamageModifier { public float Modify(float d) => d * 1.5f; }
public class IceModifier  : IDamageModifier { public float Modify(float d) => d * 0.8f; }
```

---

## L — Liskov Substitution Principle (LSP)

> Объекты базового типа можно **заменить объектами наследника** без нарушения корректности программы, без сайд эффектов.

Наследник не должен сужать контракт базового класса (бросать неожиданные исключения, игнорировать вызовы, ужесточать предусловия).

```csharp
// нарушение LSP: наследник ломает ожидание "птица умеет летать"
public class Bird { public virtual void Fly() { } }
public class Penguin : Bird
{
    public override void Fly() => throw new NotSupportedException(); // сюрприз для вызывающего
}

// решение: правильная абстракция
public interface IBird { }
public interface IFlyingBird : IBird { void Fly(); }

public class Sparrow : IFlyingBird { public void Fly() { } }
public class Penguin : IBird { }   // просто не реализует полёт
```

---

## I — Interface Segregation Principle (ISP)

> Клиента не нужно заставлять зависеть от методов, которые он **не использует**.

Лучше несколько узких интерфейсов, чем один «толстый», который вынуждает реализовывать ненужное.

```csharp
// плохо: турель обязана реализовать Move(), хотя не двигается
public interface IUnit { void Move(); void Attack(); void TakeDamage(int d); }

// хорошо: интерфейсы разбиты по способностям
public interface IMovable    { void Move(); }
public interface IAttacker   { void Attack(); }
public interface IDamageable { void TakeDamage(int d); }

public class Soldier : IMovable, IAttacker, IDamageable { /* ... */ }
public class Turret  : IAttacker, IDamageable           { /* без IMovable */ }
```

---

## D — Dependency Inversion Principle (DIP)

> Модули верхнего уровня **не зависят** от модулей нижнего уровня — оба зависят от **абстракций**.

Зависимости передаются извне (через интерфейсы), а не создаются внутри класса. База для Dependency Injection.

```csharp
// плохо: жёсткая зависимость от конкретной реализации
public class Game
{
    private readonly FileSaveSystem _save = new FileSaveSystem();
}

// хорошо: зависим от абстракции, реализацию внедряем
public interface ISaveSystem { void Save(PlayerData d); }

public class Game
{
    private readonly ISaveSystem _save;
    public Game(ISaveSystem save) => _save = save;  // подменяемо, тестируемо
}
```
