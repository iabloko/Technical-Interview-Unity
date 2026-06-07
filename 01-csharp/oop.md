[← К содержанию](../README.md)

# ООП в C#

## Четыре столпа ООП

### 1. Инкапсуляция
Сокрытие внутреннего состояния и предоставление доступа только через контролируемый интерфейс. В C# реализуется через модификаторы доступа и свойства.

```csharp
public class Player
{
    private int _health;                 // состояние скрыто

    public int Health                    // доступ через свойство
    {
        get => _health;
        private set => _health = Mathf.Max(0, value);  // инвариант: не уйдёт в минус
    }

    public void TakeDamage(int amount) => Health -= amount;
}
```

### 2. Наследование
Создание нового класса на основе существующего с переиспользованием и расширением поведения. В C# **только одиночное** наследование классов (но множественная реализация интерфейсов).

```csharp
public class Enemy : MonoBehaviour { /* ... */ }
public class Boss : Enemy { /* добавляет/переопределяет поведение */ }
```

### 3. Полиморфизм
Один интерфейс — разные реализации. Различают:
- **Статический (compile-time)** — перегрузка методов (`overload`).
- **Динамический (run-time)** — переопределение виртуальных методов (`override`).

```csharp
public abstract class Shape { public abstract float Area(); }

public class Circle : Shape
{
    public float Radius;
    public override float Area() => Mathf.PI * Radius * Radius;
}

public class Rect : Shape
{
    public float W, H;
    public override float Area() => W * H;
}

// вызывающий код не знает конкретного типа
float Total(IEnumerable<Shape> shapes) => shapes.Sum(s => s.Area());
```

### 4. Абстракция
Выделение существенных характеристик объекта и сокрытие деталей реализации. В коде — через абстрактные классы и интерфейсы.

---

## Модификаторы доступа

| Модификатор          | Где доступно                                   |
|----------------------|------------------------------------------------|
| `private`            | только внутри класса (по умолчанию для членов) |
| `protected`          | класс + наследники                             |
| `internal`           | внутри сборки (assembly)                       |
| `protected internal` | сборка ИЛИ наследники                          |
| `private protected`  | наследники внутри той же сборки                |
| `public`             | везде                                          |

---

## virtual / override / new / sealed

```csharp
public class Base
{
    public virtual void Speak() => Debug.Log("Base");
}

public class Derived : Base
{
    public override void Speak() => Debug.Log("Derived");
}

public class Shadow : Base
{
    public new void Speak() => Debug.Log("Shadow");
}
```

- `virtual` — разрешает переопределение.
- `override` — переопределяет; вызов идёт по фактическому типу объекта.
- `new` — **скрывает** метод базового класса; вызов идёт по типу ссылки (частая ловушка на собесе).
- `sealed` — запрещает дальнейшее переопределение/наследование.

```csharp
Base b = new Derived(); b.Speak();  // "Derived" (override → по объекту)
Base s = new Shadow();  s.Speak();  // "Base"    (new → по типу ссылки)
```

---

## Композиция vs наследование (важно для Unity)

Unity построен на **композиции**: объект = `GameObject` + набор компонентов. Это предпочтительнее глубоких иерархий наследования.

- **Наследование** жёстко связывает: изменение базы ломает всех наследников, легко получить «хрупкую» иерархию.
- **Композиция** гибче: поведение собирается из независимых частей, проще тестировать и переиспользовать.

```csharp
// Вместо иерархии FlyingShootingEnemy : ShootingEnemy : Enemy
// собираем поведение из компонентов:
public class Enemy : MonoBehaviour
{
    [SerializeField] private MovementComponent _movement;
    [SerializeField] private WeaponComponent _weapon;
    [SerializeField] private HealthComponent _health;
}
```

> Принцип: **«Предпочитай композицию наследованию»** (из «Banda четырёх»).

---