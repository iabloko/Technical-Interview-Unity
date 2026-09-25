[← К содержанию](../README.md)

# Input System (новый) vs legacy Input

**Input System** (пакет `com.unity.inputsystem`) — событийная система ввода, заменяющая legacy `UnityEngine.Input`. Ключевая идея: код подписывается на **абстрактные действия** (Jump, Move), а не опрашивает конкретные клавиши; привязка действий к устройствам — данные (ассет), а не код.

## Сравнение с legacy

| | Legacy `Input` | Input System |
|---|---|---|
| Модель | polling (`GetKey`, `GetAxis`) в `Update` | события + polling по действиям |
| Привязка | хардкод клавиш/осей в коде, оси в Project Settings | `InputActionAsset` — данные, редактируются без кода |
| Несколько устройств | вручную (`Joystick1Button0`...) | устройства абстрагированы, hot-plug из коробки |
| Переназначение (rebinding) | самописное | `PerformInteractiveRebinding()` встроено |
| Локальный мультиплеер | вручную | `PlayerInputManager`, спаривание устройств с игроками |
| Схемы управления | нет | control schemes (Keyboard&Mouse / Gamepad / Touch) |

Обе системы могут работать одновременно (`Active Input Handling: Both`) — полезно при миграции.

## Структура данных

```
InputActionAsset
└── Action Map (Gameplay, UI, Vehicle)         — переключаемые наборы действий
    └── Action (Move, Jump, Fire)              — абстрактное действие с типом значения
        └── Binding (<Gamepad>/leftStick, WASD-composite)   — привязка к контролам устройств
```

- **Action Map** — набор действий одного контекста; переключение контекста = `gameplayMap.Disable(); uiMap.Enable()`. Активная карта определяет, какой ввод вообще обрабатывается.
- **Action** имеет тип:
  - **Value** — непрерывное значение (`Vector2` стика); при нескольких активных контролах выбирается самый «сильный» (disambiguation);
  - **Button** — дискретное нажатие с порогом срабатывания;
  - **Pass-Through** — без disambiguation, сырой поток со всех контролов.
- **Binding** — путь к контролу (`<Gamepad>/buttonSouth`); **composite bindings** собирают значение из нескольких контролов (2D Vector из WASD).
- **Interactions** — условие срабатывания: Tap, Hold, MultiTap, SlowTap (Hold — «зажать на N секунд»).
- **Processors** — преобразование значения: deadzone стика, invert, normalize, scale.

## Control Schemes

**Схема управления** группирует биндинги по типам устройств (Keyboard&Mouse, Gamepad, Touch) и объявляет, какие устройства ей нужны. Используется для:
- автоматического определения активной схемы (на чём сейчас играют) и переключения UI-подсказок (иконки кнопок);
- спаривания устройств с игроками в локальном мультиплеере (одному игроку — геймпад №1, другому — клавиатура).

## Получение ввода в коде

**Колбэки** — у каждого действия три фазы: `started` (началось взаимодействие), `performed` (условие выполнено), `canceled` (прервано/отпущено):

```csharp
_actions.Gameplay.Jump.performed += OnJump;          // подписка
private void OnJump(InputAction.CallbackContext ctx) => _jumpRequested = true;
```

**Polling** — для непрерывных значений в `Update`:

```csharp
Vector2 move = _actions.Gameplay.Move.ReadValue<Vector2>();
bool jump = _actions.Gameplay.Jump.WasPerformedThisFrame();
```

Способы подключения ассета:
- **Generated C# class** (флажок на ассете) — типобезопасная обёртка, рекомендуемый для кода вариант;
- **PlayerInput** компонент — без кода, режимы доставки: Send Messages / Broadcast / Unity Events / **Invoke C# Events** (последний — наименьшие накладные расходы);
- прямые ссылки `InputActionReference` в инспекторе.

Карты/действия должны быть **включены** (`Enable()`), иначе события не приходят. Не забывать отписываться и `Disable()` при уничтожении объекта.

## Ввод и FixedUpdate

События ввода по умолчанию обрабатываются **перед `Update`** (`Update Mode: Process in Dynamic Update`). Кадровый паттерн для физики прежний: считать ввод в `Update` (или в колбэке выставить флаг), применить силы в `FixedUpdate` (см. [физика](physics.md)). `WasPerformedThisFrame()` в `FixedUpdate` ненадёжен: `FixedUpdate` может выполниться 0 или несколько раз за кадр — нажатие потеряется или применится дважды; поэтому флаг, сбрасываемый после применения.

## Rebinding (переназначение клавиш)

```csharp
_action.Disable();                                   // на время ребинда действие выключают
_rebind = _action.PerformInteractiveRebinding()
    .WithControlsExcluding("<Mouse>/position")
    .OnComplete(op => { op.Dispose(); _action.Enable(); })
    .Start();
```

Сохранение: `actions.SaveBindingOverridesAsJson()` / `LoadBindingOverridesFromJson()` — оверрайды поверх ассета, в `PlayerPrefs` или файл сохранения (см. [сохранения](save-systems.md)).

## Senior-нюансы

- **UI**: для uGUI нужен `InputSystemUIInputModule` вместо `StandaloneInputModule`; конфликт «прыжок и клик по UI» решают отдельной картой UI + проверкой `EventSystem.IsPointerOverGameObject` или приоритетом карт.
- **Утечки подписок**: лямбда в `performed` без отписки держит объект; отписываться симметрично подписке (подписка в `OnEnable` — отписка в `OnDisable`, в `Awake` — в `OnDestroy`; см. [conventions](conventions.md)).
- **Disambiguation у Value-действий**: два геймпада/контрола — значение берётся с активнейшего; для сырого мультитач/мультидевайс потока — Pass-Through.
- **`InputSystem.onAnyButtonPress`** — «нажми любую кнопку», определение последнего активного устройства для подсказок UI.
- **Device hot-swap**: `InputUser.onChange` / `PlayerInput.onControlsChanged` — геймпад отключился посреди игры → пауза и подсказка.

## Что спрашивают на собеседовании

- Чем Input System принципиально отличается от legacy (события и абстракция действий vs polling клавиш; биндинги — данные).
- Иерархия ассета: action map → action → binding; зачем нужны maps (контексты Gameplay/UI).
- Типы действий Value / Button / Pass-Through и что такое disambiguation.
- Фазы started / performed / canceled; чем interaction отличается от processor.
- Зачем control schemes (определение активного устройства, локальный мультиплеер).
- Как сделать переназначение клавиш и где хранить оверрайды.
- Как корректно сочетать событийный ввод с `FixedUpdate` (флаг-буфер, а не `WasPerformedThisFrame` в физике).

---