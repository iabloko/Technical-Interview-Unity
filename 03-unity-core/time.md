[← К содержанию](../README.md)

# Время и тайминг кадра

## Основные значения `Time`

| Свойство | Что возвращает | Масштабируется `timeScale` |
|---|---|---|
| `Time.time` | время с запуска на начало кадра | да |
| `Time.deltaTime` | длительность прошлого кадра (в `FixedUpdate` — `fixedDeltaTime`) | да |
| `Time.fixedDeltaTime` | шаг физики (по умолчанию 0.02 с) | нет (это настройка шага) |
| `Time.fixedTime` | время симуляции физики | да |
| `Time.unscaledTime` / `unscaledDeltaTime` | то же, но без `timeScale` | нет |
| `Time.realtimeSinceStartup` | реальное время с запуска (идёт и в паузе редактора) | нет |
| `Time.frameCount` | номер кадра | — |

`Time.time` и `deltaTime` фиксируются **на начало кадра** и одинаковы для всех вызовов внутри кадра — детерминированность внутри кадра гарантирована.

## deltaTime и независимость от частоты кадров

Любое движение/изменение «в секунду» умножается на `deltaTime`, иначе скорость зависит от FPS:

```csharp
transform.position += velocity * Time.deltaTime;   // одинаковая скорость при 30 и 144 FPS
```

**Нюанс с `Lerp` в Update:** `Lerp(a, b, k * Time.deltaTime)` — экспоненциальное затухание, и его скорость **зависит от FPS** (ошибка накапливается нелинейно). Кадронезависимая форма затухания:

```csharp
float t = 1f - Mathf.Exp(-k * Time.deltaTime);
current = Mathf.Lerp(current, target, t);
```

## Аккумулятор фиксированного шага

Физика и `FixedUpdate` идут с постоянным шагом `fixedDeltaTime` независимо от FPS. Механизм:

1. В начале кадра время кадра добавляется в **аккумулятор**.
2. Пока `аккумулятор >= fixedDeltaTime`: выполняется `FixedUpdate` + шаг физики, из аккумулятора вычитается `fixedDeltaTime`.
3. Затем выполняется `Update` (см. [lifecycle](lifecycle.md)).

Следствия:
- При FPS > 50 (шаг 0.02) в некоторых кадрах `FixedUpdate` **не вызывается вовсе**; при FPS < 50 — **несколько раз за кадр**.
- Остаток аккумулятора меньше шага переносится на следующий кадр → видимая физика идёт «между» шагами симуляции; для плавности у `Rigidbody` включают **Interpolate** (интерполяция позы между двумя последними шагами).

**Maximum Allowed Timestep** (`Time.maximumDeltaTime`, по умолчанию 0.3333 с) — потолок времени, добавляемого в аккумулятор за кадр. Защита от **«спирали смерти»**: длинный кадр → много шагов физики → кадр ещё длиннее → ещё больше шагов. Цена ограничения: при тяжёлых кадрах симуляция **замедляется относительно реального времени** (теряет время, а не стабильность).

## timeScale

`Time.timeScale` масштабирует игровое время: `deltaTime`, `time`, частоту `FixedUpdate` (шаг остаётся `fixedDeltaTime` в игровом времени, но наступает реже/чаще в реальном).

- `timeScale = 0` — пауза: `FixedUpdate` **не вызывается вовсе**, `Update`/`LateUpdate` продолжаются с `deltaTime == 0`.
- Slow-motion: `timeScale = 0.5` — физика идёт вдвое реже в реальном времени, но корректно (шаг в игровом времени неизменен).
- Что должно работать на паузе/в slow-mo — переводят на **unscaled**-время:
  - UI-анимации: `Animator.updateMode = UnscaledTime` (см. [анимация](animation.md));
  - твины: `DOTween` `SetUpdate(true)` (см. [DOTween](../11-tools/dotween.md));
  - задержки: `UniTask.Delay(..., DelayType.UnscaledDeltaTime)` (см. [async](../05-async/async.md));
  - корутины: `WaitForSecondsRealtime` вместо `WaitForSeconds`.

## Ограничение FPS: vSyncCount и targetFrameRate

- `QualitySettings.vSyncCount` — синхронизация с разверткой дисплея (1 = каждый VBlank). На десктопных платформах при `vSyncCount > 0` `targetFrameRate` **игнорируется**. На iOS и Android наоборот: `vSyncCount` игнорируется, частоту кадров задаёт `targetFrameRate`.
- `Application.targetFrameRate` — программный потолок FPS (на десктопе работает при `vSyncCount = 0`). На мобильных — стандартный способ ограничить FPS ради энергопотребления/нагрева (см. [мобильная оптимизация](../06-performance/mobile-optimization.md)); по умолчанию мобильные платформы рендерят на 30.

## Senior-нюансы

- **Уменьшать `fixedDeltaTime`** (например, до 0.01) — точнее физика, но вдвое дороже CPU; повышать — дешевле, но туннелирование и нестабильность контактов (см. [физика](physics.md), CCD).
- **Хитчи и `deltaTime`**: однократный длинный кадр даёт большой `deltaTime` → телепортация объектов, движущихся кодом. `maximumDeltaTime` ограничивает это и для `deltaTime` обычного Update.
- Таймеры геймплея — складывать `deltaTime`, а не сравнивать `Time.time` с float-порогом: точность `float` у `Time.time` деградирует на долгих сессиях (часы аптайма — мобильные/выживалки). Для длинных сессий — `Time.timeAsDouble` / `unscaledTimeAsDouble`.
- `timeScale = 0` останавливает и `Time.time` — кулдауны на `Time.time` «замерзают» на паузе; решить через unscaled или осознанно оставить.
- Реальная длительность для метрик/лога — `Time.realtimeSinceStartup` или `Stopwatch`, не `Time.time`.

## Что спрашивают на собеседовании

- Чем `deltaTime` отличается от `fixedDeltaTime`; что возвращает `Time.deltaTime` внутри `FixedUpdate` (значение `fixedDeltaTime`).
- Как работает аккумулятор: почему `FixedUpdate` может выполниться 0 или несколько раз за кадр.
- Что такое спираль смерти и как её предотвращает `maximumDeltaTime` (ценой замедления симуляции).
- Что произойдёт при `timeScale = 0` с `Update` и `FixedUpdate`; как сделать UI, работающий на паузе.
- Почему движение без умножения на `deltaTime` зависит от FPS; чем плох `Lerp(a, b, k * deltaTime)` и как сделать кадронезависимое затухание.
- Зачем `Rigidbody.Interpolate`, если физика и так детерминирована (рендер между шагами симуляции).
- `vSyncCount` vs `targetFrameRate` — что приоритетнее и когда какой использовать (на мобильных действует только `targetFrameRate`).

---