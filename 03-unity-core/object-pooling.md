х[← К содержанию](../README.md)

# Object Pooling (пул объектов)

Пул переиспользует заранее созданные объекты вместо постоянного `Instantiate`/`Destroy`. Решает две проблемы:

1. **`Instantiate`/`Destroy` дороги** — создание GameObject, `Awake`/`OnEnable`, регистрация компонентов; уничтожение порождает мусор.
2. **`Destroy` нагружает [GC](unity-gc.md)** — освобождённые объекты копятся и вызывают сборку → спайки кадра.

Типичные кандидаты: пули, частицы, враги, всплывающий UI-текст, аудиоисточники — всё, что часто появляется и исчезает.

## Принцип

- Берём из пула (`Get`): объект активируется (`SetActive(true)`), сбрасывается состояние.
- Возвращаем в пул (`Release`): объект деактивируется (`SetActive(false)`), а не уничтожается.
- При нехватке — пул либо создаёт новый объект (растущий пул), либо переиспользует самый старый (фиксированный).

```csharp
var bullet = _pool.Get();
bullet.transform.position = muzzle.position;
// при попадании / по таймеру:
_pool.Release(bullet);
```

## Встроенный пул (Unity 2021+)

`UnityEngine.Pool.ObjectPool<T>` / `LinkedPool<T>` — готовая реализация с колбэками:

```csharp
_pool = new ObjectPool<Bullet>(
    createFunc:   () => Instantiate(_prefab),
    actionOnGet:  b => b.gameObject.SetActive(true),
    actionOnRelease: b => b.gameObject.SetActive(false),
    actionOnDestroy: b => Destroy(b.gameObject),
    defaultCapacity: 50, maxSize: 200);
```

## Нюансы (важно)

- **Сброс состояния обязателен.** Объект из пула несёт прежнее состояние (здоровье, скорость, корутины, подписки). Чистить при `Get` или `Release`, иначе плавающие баги.
- **Двойной `Release`** одного объекта ломает пул (объект выдадут дважды). Защищаться флагом/проверкой.
- **`OnEnable`/`OnDisable`** вызываются на `SetActive`, а `Awake`/`Start` — нет (объект не пересоздаётся). Логику переинициализации вешать на `OnEnable` или явный `Reset`.
- Прогрев (prewarm) на загрузке, чтобы не платить за создание во время геймплея.
- Частицы — `ParticleSystem` со `Stop Action: Disable` хорошо ложится в пул.

## Что спрашивают на собеседовании

- Зачем пул (стоимость `Instantiate`/`Destroy` и нагрузка на GC).
- Что обязательно делать с объектом при возврате/выдаче (сброс состояния).
- Какие методы lifecycle вызываются у пулящегося объекта (`OnEnable`/`OnDisable`, не `Awake`/`Start`).
- Чем опасен двойной `Release`.

---