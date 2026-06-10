[← К содержанию](../README.md)

# Система анимации: Animator, Blend Trees, Playables, Root Motion, IK

## Mecanim: Animator и AnimatorController

**Animator** — компонент, проигрывающий анимацию на объекте. **AnimatorController** — ассет с конечным автоматом состояний: states (каждое ссылается на `AnimationClip` или Blend Tree), transitions между ними и параметры.

**Параметры** (`Float`, `Int`, `Bool`, `Trigger`) — вход автомата; код выставляет их, переходы по ним срабатывают:

```csharp
private static readonly int SpeedParam = Animator.StringToHash("Speed"); // хэш вместо строки — без поиска по имени на каждый вызов
_animator.SetFloat(SpeedParam, velocity.magnitude);
```

**Переходы (transitions):**
- **Has Exit Time** — переход возможен только после указанной доли клипа; для прерываемых переходов (реакция на ввод) его выключают.
- **Transition Duration** — длительность кроссфейда (блендинг между состояниями).
- **Interruption Source** — может ли другой переход прервать текущий.
- `Trigger` остаётся взведённым, если переход не сработал — частый источник «отложенных» срабатываний; сбрасывать `ResetTrigger`.

**Слои (layers):** независимые автоматы, результат смешивается по весу. **Avatar Mask** ограничивает слой частью скелета (верхняя половина — стрельба, нижняя — бег). Режимы: **Override** (заменяет нижние слои) и **Additive** (добавляет дельту от референсной позы).

**Avatar, Humanoid vs Generic:**
- **Generic** — клип привязан к конкретной иерархии костей.
- **Humanoid** — кости маппятся на стандартизированный мышечный риг (muscle space) → **ретаргетинг**: один клип проигрывается на любом humanoid-персонаже. Дороже Generic по CPU.

## Blend Trees

Состояние, которое **смешивает несколько клипов по параметрам** вместо дискретных переходов — непрерывная локомоция без взрыва числа состояний.

| Тип | Параметры | Применение |
|---|---|---|
| 1D | один float | idle → walk → run по скорости |
| 2D Simple Directional | два float | движение по направлениям, по одному клипу на направление |
| 2D Freeform Directional | два float | то же + несколько клипов на направление (разные скорости) |
| 2D Freeform Cartesian | два float | параметры не являются направлением (скорость + угловая скорость) |

Клипы в дереве должны быть согласованы по длительности/фазе шага, иначе при смешивании ноги «плывут».

## Root Motion

**Root motion** — смещение и поворот персонажа берутся **из самой анимации** (движение корневой кости), а не из кода. Анимация двигает transform → движение точно совпадает с клипом, нет скольжения ног.

- `Animator.applyRootMotion = true` — движок применяет дельту к transform автоматически.
- `OnAnimatorMove()` — колбэк для **ручного** применения: читаешь `animator.deltaPosition` / `deltaRotation` и применяешь через `CharacterController.Move` или `Rigidbody.MovePosition` (для согласования с физикой).
- Альтернатива — **in-place** анимации + движение кодом: проще для геймплея (точный контроль скорости, сетевая синхронизация), но требует подгонять скорость анимации под скорость движения, иначе foot sliding.

## IK (инверсная кинематика)

Прямая кинематика: поза задаётся углами костей из клипа. **IK** решает обратную задачу: по целевой позиции эффектора (кисть, стопа) вычислить углы костей цепочки.

**Встроенный Humanoid IK** — только для Humanoid-ригов, через `OnAnimatorIK()` (на слое включён **IK Pass**):

```csharp
private void OnAnimatorIK(int layerIndex)
{
    _animator.SetIKPositionWeight(AvatarIKGoal.RightHand, 1f);
    _animator.SetIKPosition(AvatarIKGoal.RightHand, _target.position);  // дотянуться рукой до цели
    _animator.SetLookAtWeight(1f);
    _animator.SetLookAtPosition(_lookTarget.position);
}
```

Применение: стопы на неровной поверхности (foot placement), руки на оружии/рычагах, взгляд на цель.

## Animation Rigging (пакет)

Пакет **Animation Rigging** — constraint-системы поверх Animator, исполняются через Animation C# Jobs (вне главного потока):

- `TwoBoneIKConstraint` — IK-цепочка из двух костей (рука, нога), работает и на Generic.
- `MultiAimConstraint` — наведение кости на цель (голова, торс при прицеливании).
- `DampedTransform`, `OverrideTransform` и др.
- Веса констрейнтов анимируются → плавное включение/выключение процедурных эффектов поверх клипов.

Это стандартный способ процедурной анимации (прицеливание, взгляд, хват) в современных проектах вместо ручного `OnAnimatorIK`.

## Playables API

Низкоуровневый API: анимация описывается **графом** (`PlayableGraph`) из узлов — `AnimationClipPlayable`, `AnimationMixerPlayable`, `AnimationLayerMixerPlayable` — с выходом в `AnimationPlayableOutput` на Animator.

```csharp
var graph = PlayableGraph.Create("Custom");
var clipPlayable = AnimationClipPlayable.Create(graph, clip);
var output = AnimationPlayableOutput.Create(graph, "out", _animator);
output.SetSourcePlayable(clipPlayable);
graph.Play();
// ...
graph.Destroy();   // обязательно — граф держит нативные ресурсы
```

**Зачем, если есть AnimatorController:**
- проигрывание клипов **без** ассета контроллера (динамический контент: клип пришёл из Addressables);
- смешивание с произвольной логикой весов в рантайме, кастомные структуры блендинга;
- на Playables построены **Timeline** и сторонние решения (Animancer);
- граф может смешивать не только анимацию (аудио, скрипты — `ScriptPlayable`).

Минусы: ручное управление графом и его временем жизни (`graph.Destroy()`), больше кода.

## Производительность

- **Culling Mode** у Animator: `Cull Update Transforms` / `Cull Completely` — не анимировать невидимых (осторожно с root motion: `Cull Completely` останавливает и его).
- **Optimize Game Objects** (в настройках рига) — убирает Transform-иерархию костей из сцены, скиннинг идёт по нативным данным; экспонировать только нужные кости (сокеты оружия).
- Параметры — через `Animator.StringToHash`, не строками.
- Animator с большим контроллером дороже простого `Animation` (legacy) на массовке; для толп — Playables с минимальным графом, GPU-скиннинг, или вертексная анимация (VAT).
- **Update Mode**: `Normal` (Update, масштабируется `timeScale`), `Animate Physics` (FixedUpdate — для анимируемых коллайдеров/Rigidbody), `Unscaled Time` (UI, не зависит от паузы — см. [время](time.md)).
- **Animation Events** вызывают метод по имени (рефлексия, поиск по компонентам) — на горячих путях учитывать.

## Что спрашивают на собеседовании

- Из чего состоит AnimatorController (состояния, переходы, параметры, слои); зачем Avatar Mask и чем Override отличается от Additive.
- Humanoid vs Generic: что даёт ретаргетинг и что он стоит.
- Зачем Blend Tree вместо переходов между состояниями; типы 2D-деревьев.
- Что такое root motion, как применить его вручную (`OnAnimatorMove`) и когда выбрать in-place + код.
- Как работает встроенный IK и почему он только для Humanoid; что даёт Animation Rigging.
- Зачем Playables API, если есть AnimatorController (динамические клипы, кастомный блендинг, Timeline/Animancer).
- Почему `Trigger` может сработать «позже» (остаётся взведённым); `ResetTrigger`.
- Как удешевить анимацию массовки (culling, Optimize Game Objects, hashing, GPU-скиннинг).

---