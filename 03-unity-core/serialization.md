[← К содержанию](../README.md)

# Сериализация в Unity

Сериализация — преобразование состояния объекта в данные, которые Unity хранит в ассетах/сценах и показывает в Inspector. На ней держатся Inspector, префабы, сцены, `ScriptableObject`, Undo, hot-reload скриптов.

## Что сериализуется

Поле сериализуется, если оно:
- `public` **или** помечено `[SerializeField]`;
- **не** `static`, `const`, `readonly`;
- имеет сериализуемый тип.

`[System.NonSerialized]` явно исключает public-поле.

## Какие типы сериализуемы

- Примитивы, `string`, `enum`.
- Unity-типы: `Vector*`, `Color`, `Quaternion`, `AnimationCurve`, и т. п.
- Ссылки на наследников `UnityEngine.Object` (`GameObject`, компоненты, ассеты) — хранятся как ссылка.
- Свои `class`/`struct` с атрибутом `[System.Serializable]`.
- Массивы и `List<T>` из сериализуемых типов.

## Чего движок НЕ сериализует (частый вопрос)

- `Dictionary<K,V>` — не сериализуется (см. обход ниже).
- Поля интерфейсного типа и `object` (нет конкретного типа) — кроме `[SerializeReference]`.
- Свойства (properties) — сериализуются только поля.
- `static`, `const`, `readonly`.
- Обобщённые пользовательские типы (до определённых версий — ограниченно).
- Вложенность ограничена по глубине; циклические ссылки на обычные `[Serializable]`-классы дублируются, а не разделяются (см. `[SerializeReference]`).

## [SerializeReference]

Позволяет сериализовать поле **по ссылке на управляемый объект** с сохранением фактического (полиморфного) типа и общих ссылок. Так сериализуют поля интерфейсов/абстрактных классов и графы объектов.

```csharp
[SerializeReference] private IAbility _ability;   // конкретный тип сохранится
```

## ISerializationCallbackReceiver

Хук вокруг (де)сериализации. Стандартный приём — хранить несериализуемую структуру (например, `Dictionary`) в сериализуемых списках:

```csharp
public class Lookup : MonoBehaviour, ISerializationCallbackReceiver
{
    [SerializeField] private List<string> _keys = new();
    [SerializeField] private List<int> _values = new();
    private Dictionary<string, int> _map = new();

    public void OnBeforeSerialize() { /* map → keys/values */ }
    public void OnAfterDeserialize() { /* keys/values → map */ }
}
```

Колбэки могут вызываться из не-главного потока — внутри только работа с данными, без Unity API.

## Связанные нюансы

- Изменение имени сериализованного поля теряет данные; сохранить связь — `[FormerlySerializedAs("old")]`.
- Сериализация — причина, по которой Unity требует поля, а не свойства, и почему «магически» появляются значения после переименования скрипта.

## Что спрашивают на собеседовании

- Какие условия делают поле сериализуемым (`[SerializeField]`, не static/const/readonly).
- Почему `Dictionary` не сериализуется и как обойти (`ISerializationCallbackReceiver` + два списка).
- Зачем `[SerializeReference]` (полиморфизм, интерфейсы, разделяемые ссылки).
- Почему сериализуются поля, а не свойства.

---