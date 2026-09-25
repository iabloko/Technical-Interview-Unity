[← К содержанию](../README.md)

# Презентационные паттерны: MVC / MVP / MVVM

Семейство паттернов, отделяющих **данные/логику от отображения**. Цель — UI не содержит бизнес-логики, логика не знает о конкретных виджетах → тестируемость и слабая связанность (см. [coupling](../02-architecture/coupling-decoupling.md)).

## Общие роли

- **Model** — данные и бизнес-логика, независимы от UI.
- **View** — отображение (в Unity: `MonoBehaviour` с ссылками на UI-элементы, `Button`, `Text`/TMP).

Различие — в посреднике между Model и View.

## MVC

- **Controller** принимает ввод, меняет Model; View читает Model.
- Границы Controller/View в играх размыты; в чистом виде в Unity применяется редко.

## MVP (часто выбирают в Unity)

- **Presenter** — посредник: получает события от View, дёргает Model, обновляет View через её интерфейс.
- View **пассивна** (Passive View): не содержит логики, реализует интерфейс (`IHealthView { void SetHealth(int) }`), Presenter работает с интерфейсом, не с конкретным виджетом.
- View и Model **не знают друг о друге**; всё через Presenter.

```csharp
public interface IHealthView { void Render(int current, int max); }

public class HealthPresenter
{
    private readonly IHealthView _view;
    private readonly Health _model;

    public HealthPresenter(IHealthView view, Health model)
    {
        _view = view;
        _model = model;
        _model.Changed += () => _view.Render(_model.Current, _model.Max);
    }
}
```

Presenter — обычный C#-класс без `MonoBehaviour` → юнит-тестируется с mock-View (см. [тестирование](../09-testing/testing.md)).

## MVVM

- **ViewModel** выставляет состояние через **наблюдаемые свойства**; View **связывается** (data binding) с ними и обновляется автоматически.
- View декларативно подписана на ViewModel; ручного `view.SetX()` нет.
- В Unity нет встроенного binding для uGUI; реализуют через [UniRx](../11-tools/unirx.md) (`ReactiveProperty`) или **UI Toolkit** (есть data binding). 

```csharp
// ViewModel с UniRx
public ReactiveProperty<int> Score = new(0);
// View
viewModel.Score.Subscribe(v => _label.text = v.ToString()).AddTo(this);
```

## Сравнение

| | Посредник | Связь View↔логика | Binding |
|---|---|---|---|
| MVC | Controller | View читает Model | нет |
| MVP | Presenter | через интерфейс View | ручной |
| MVVM | ViewModel | подписка на свойства | автоматический |

## Что спрашивают на собеседовании

- Зачем отделять UI от логики (тестируемость, связанность).
- Разница MVP vs MVVM (ручное обновление через интерфейс vs data binding на наблюдаемых свойствах).
- Почему Presenter/ViewModel делают не-`MonoBehaviour` (юнит-тесты).
- Как реализуют binding в Unity (UniRx, UI Toolkit).

---