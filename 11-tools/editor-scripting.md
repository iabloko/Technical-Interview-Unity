[← К содержанию](../README.md)

# Editor scripting (расширения редактора)

Код, расширяющий сам редактор Unity: кастомные инспекторы, окна, инструменты. Senior часто пишет тулинг для команды (геймдизайнеров, художников).

## Где живёт

- В папке **`Editor/`** с editor-only [`asmdef`](../03-unity-core/assembly-definitions.md) (`includePlatforms: ["Editor"]`), чтобы код **не попадал в билд** (использует `UnityEditor`, недоступный в рантайме).
- `#if UNITY_EDITOR` — для editor-кода, который вынужденно лежит рядом с рантайм-кодом.

## Основные инструменты

| API | Для чего |
|---|---|
| `Editor` + `[CustomEditor(typeof(T))]` | кастомный Inspector компонента (`OnInspectorGUI`) |
| `EditorWindow` | собственное окно-инструмент |
| `PropertyDrawer` + `[CustomPropertyDrawer]` | отрисовка одного типа/атрибута в Inspector |
| `[MenuItem("Tools/…")]` | пункт меню, запускающий команду |
| `ScriptableWizard` | простые мастера-формы |
| Gizmos (`OnDrawGizmos`) | отрисовка в Scene view (это рантайм-хук, не Editor-сборка) |
| `AssetPostprocessor` | хук на импорт ассетов |

```csharp
[CustomEditor(typeof(Spawner))]
public class SpawnerEditor : Editor
{
    public override void OnInspectorGUI()
    {
        DrawDefaultInspector();
        var spawner = (Spawner)target;
        if (GUILayout.Button("Spawn now"))
            spawner.SpawnOne();
    }
}
```

## SerializedObject / SerializedProperty (важно)

Правильный способ менять значения в инспекторе — через `SerializedObject`/`SerializedProperty`, а не напрямую поля объекта:
- автоматически поддерживает **Undo**, multi-object editing, пометку сцены dirty;

```csharp
serializedObject.Update();
EditorGUILayout.PropertyField(serializedObject.FindProperty("_speed"));
serializedObject.ApplyModifiedProperties();
```

Прямое изменение `target.field` обходит Undo и не помечает объект изменённым (правки могут не сохраниться).

## Odin Inspector (если подключён)

При наличии Odin предпочитают его атрибуты (`[ShowInInspector]`, `[Button]`, `[ValueDropdown]`, `OdinEditorWindow`) вместо ручного `OnInspectorGUI` — меньше boilerplate. Проверять наличие в проекте.

## UI Toolkit для редактора

Современный путь editor-UI — UXML/USS + `CreateInspectorGUI()` вместо IMGUI (`OnInspectorGUI`). IMGUI по-прежнему распространён в существующих проектах.

## Что спрашивают на собеседовании

- Почему editor-код в `Editor/`-папке/сборке (не попадает в билд).
- Чем `CustomEditor` отличается от `PropertyDrawer` (компонент целиком vs один тип/атрибут).
- Зачем `SerializedObject`/`SerializedProperty` (Undo, multi-edit, dirty) вместо прямого доступа к полям.
- Как добавить инструмент в меню (`[MenuItem]`).

---