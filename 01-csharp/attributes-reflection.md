[← К содержанию](../README.md)

# Атрибуты и рефлексия

## Атрибуты

Атрибут — метаданные, прикреплённые к коду (типу, методу, полю) и доступные в рантайме через рефлексию. Сам по себе атрибут ничего не делает — его считывает другой код (рантайм, движок, инструмент).

```csharp
[Serializable]
public class Config
{
    [SerializeField] private int _level;
    [Range(0, 100)] public float Volume;
    [Obsolete("Use NewMethod")] public void OldMethod() { }
}
```

Примеры в Unity: `[SerializeField]`, `[CreateAssetMenu]`, `[RequireComponent]`, `[RuntimeInitializeOnLoadMethod]`, `[ContextMenu]`, `[Header]`/`[Tooltip]` — все они читаются движком/редактором через рефлексию (см. [сериализация](../03-unity-core/serialization.md), [conventions](../03-unity-core/conventions.md)).

Свой атрибут — наследник `System.Attribute`, ограничивается целями через `[AttributeUsage]`.

## Рефлексия

Рефлексия — чтение метаданных типов и обращение к членам в рантайме: получить `Type`, перечислить поля/методы, прочитать атрибуты, создать экземпляр, вызвать метод по имени.

```csharp
Type t = obj.GetType();
foreach (var f in t.GetFields(BindingFlags.Instance | BindingFlags.NonPublic))
    if (f.IsDefined(typeof(SerializeField), false)) { /* … */ }

object inst = Activator.CreateInstance(t);
MethodInfo m = t.GetMethod("Run");
m.Invoke(inst, args);
```

## Стоимость и ограничения (важно)

- **Рефлексия медленная.** Поиск членов, `Invoke`, `CreateInstance` — на порядки дороже прямого вызова. Не использовать в hot path. Если нужна — кешировать `MemberInfo`/делегаты (скомпилировать в `Delegate`/expression tree один раз).
- **Боксинг** при работе со значимыми типами через `object`.
- **AOT/IL2CPP** (см. [il2cpp](../03-unity-core/il2cpp-mono.md)): `Reflection.Emit` (генерация кода в рантайме) не работает; код, доступный только через рефлексию, может быть вырезан managed stripping → защищать `[Preserve]`/`link.xml`.

## Где это в Unity под капотом

Сериализация, Inspector, drag-and-drop, `[Inject]` в [DI](../02-architecture/di.md)/Zenject, тест-раннер, многие редакторные инструменты используют рефлексию и атрибуты. Senior понимает, что «магия» Inspector'а и DI — это чтение атрибутов рефлексией, и что это стоит производительности на старте.

## Что спрашивают на собеседовании

- Что такое атрибут и кто его «исполняет» (никто сам по себе — читается рефлексией).
- Что умеет рефлексия и почему она дорогая.
- Как ускорить рефлексию (кеш `MemberInfo`, компиляция в делегаты).
- Ограничения рефлексии под IL2CPP/AOT (Emit, stripping).

---