[← К содержанию](../README.md)

# DOTween

DOTween — твин-движок для анимации значений во времени (позиция, цвет, alpha, числа, текст) без ручных корутин-лерпов. Дефолтный инструмент анимации в проектах этого пользователя.

## Зачем вместо корутины

Корутина, которая каждый кадр лерпит значение, — это ручной код, аллокации `WaitForSeconds`/`yield` и шаблон, повторяемый везде. DOTween даёт декларативные шорткаты, easing, последовательности и управление жизненным циклом.

```csharp
transform.DOMove(target, 1f).SetEase(Ease.OutQuad);
image.DOFade(0f, 0.3f);
_tmpText.DOText("Готово!", 0.5f);   // печать текста
```

## Основное

- **Shortcut-твины**: `DOMove`, `DOLocalMove`, `DOScale`, `DORotate`, `DOFade`, `DOColor`, `DOText` (TMP), `DOValue` для произвольного значения.
- **Easing**: `SetEase(Ease.X)` или AnimationCurve.
- **Sequence** — композиция:

```csharp
DOTween.Sequence()
    .Append(transform.DOMoveX(5f, 1f))
    .Join(image.DOFade(1f, 1f))      // параллельно с предыдущим
    .AppendInterval(0.5f)
    .AppendCallback(() => Debug.Log("done"));
```

`Append` — последовательно, `Join` — параллельно, `Insert` — в конкретное время.

## Жизненный цикл (важно — частый баг)

Твин живёт в глобальном менеджере DOTween, а не на объекте. Если объект уничтожен, а твин ещё идёт и обращается к нему → `MissingReferenceException`. Поэтому **каждый твин на объекте обязан быть привязан или убит**:

- `tween.SetLink(gameObject)` — автоубийство при уничтожении объекта (предпочтительно).
- либо хранить `Tween` и `Kill()` в `OnDisable`/`OnDestroy`.
- `SetAutoKill(false)` — твин не уничтожается после завершения (для переиспользования через `Restart()`), но тогда `Kill` вручную.

## Производительность

- Не строить твины/sequence в `Update` — создавать по событию или переиспользовать (`Restart()`); см. [производительность](../06-performance/profiling-methodology.md).
- Заранее задать ёмкость пула: `DOTween.SetTweensCapacity(...)`, чтобы пул не рос в рантайме (аллокации).

## Интеграция с async

```csharp
await transform.DOMove(target, 1f).ToUniTask(cancellationToken: ct);
```

`ToUniTask` — ожидание твина через [UniTask](../05-async/async.md); не использовать `WaitForCompletion()` (блокирует поток).

## Что спрашивают на собеседовании

- Зачем DOTween вместо корутин-лерпов.
- Главный риск (твин переживает объект → `MissingReferenceException`) и как чинить (`SetLink`/`Kill`).
- `Append` vs `Join` в Sequence.
- Как ждать твин в async (`ToUniTask`) и почему не `WaitForCompletion`.

---