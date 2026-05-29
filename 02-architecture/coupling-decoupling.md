[← К содержанию](../README.md)

# Связанность (Coupling / Decoupling)

**Coupling (связанность)** — степень, в которой один модуль зависит от другого. Цель хорошей архитектуры — **слабая связанность** (loose coupling): модули знают друг о друге как можно меньше, поэтому их легко менять, тестировать и переиспользовать независимо.

> Связанность почти всегда идёт в паре с **cohesion (связностью внутри модуля)**. Идеал: **низкая связанность между модулями + высокая связность внутри модуля**.

---

## Сильная связанность (tight coupling) — чем плоха

Класс напрямую зависит от **конкретных** реализаций других классов.

```csharp
// Player знает о конкретных UIManager, AudioManager, GameManager
public class Player : MonoBehaviour
{
    void Die()
    {
        FindObjectOfType<UIManager>().ShowGameOver();
        FindObjectOfType<AudioManager>().Play("death");
        FindObjectOfType<GameManager>().RestartLevel();
    }
}
```

Проблемы:
- изменение `UIManager` может сломать `Player`;
- `Player` нельзя переиспользовать или протестировать без всех трёх классов;
- жёсткие ссылки (`FindObjectOfType`, прямые поля) → хрупкая «паутина» зависимостей.

---

## Слабая связанность (decoupling) — как достичь

### 1. Программируй на интерфейсы, а не на реализации
Зависимость от абстракции (см. [SOLID → DIP](solid.md)) позволяет подменять реализацию.

```csharp
public interface IDamageable { void TakeDamage(int amount); }

public class Weapon
{
    public void Hit(IDamageable target) => target.TakeDamage(10); // не знает конкретный тип цели
}
```

### 2. События / Observer — издатель не знает о подписчиках
`Player` просто сообщает «я умер», а кто и как реагирует — его не касается.

```csharp
public class Player : MonoBehaviour
{
    public event Action Died;
    void Die() => Died?.Invoke();
}

// подписчики решают сами, Player о них ничего не знает
player.Died += ui.ShowGameOver;
player.Died += audio.PlayDeath;
```

### 3. Dependency Injection вместо `new` / `FindObjectOfType`
Зависимости передаются извне (конструктор/`[Inject]`), а не создаются внутри. См. [Dependency Injection](di.md).

### 4. Посредник / шина событий (Mediator / Event Bus)
Модули общаются через центральный посредник, не ссылаясь друг на друга напрямую.

### 5. ScriptableObject-архитектура (Unity)
События и общие переменные выносят в **ScriptableObject**-ассеты: сцены и префабы ссылаются на ассет, а не друг на друга — связи разрываются на уровне данных.

---

## Чем измеряется

- **Afferent / efferent зависимости** — сколько модулей зависит от тебя и от скольких зависишь ты.
- Хорошие признаки слабой связанности: класс легко **замокать** в тесте, заменить реализацию, переиспользовать в другом проекте.

---