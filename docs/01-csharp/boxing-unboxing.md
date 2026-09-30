[← К содержанию](../README.md)

# Boxing / Unboxing

**Boxing (упаковка)** — преобразование value-типа в ссылочный (`object` или интерфейс): значение копируется в **кучу**.
**Unboxing (распаковка)** — обратное преобразование из объекта в value-тип. Частый источник скрытого мусора и нагрузки
на GC.

```csharp
int n = 42;
object boxed = n;      // boxing: значение копируется в кучу
int back = (int)boxed; // unboxing: копирование обратно + проверка типа
```

## Где прячется

- `ArrayList`, `Hashtable` и прочие не-дженерик коллекции;
- `string.Format` и интерполяция со value-типами: в C# 9 (версия языка в Unity) `$"{x}"` компилируется в `string.Format(string, object)`. Конкатенация `"a" + x` не боксит — компилятор (Roslyn с 2019 г.) вызывает `x.ToString()`, но строка всё равно аллоцируется;
- передача `struct` в параметр типа `object`;
- вызов метода value-типа через **интерфейс** (экземпляр боксится);
- `foreach` по коллекции, чей энумератор возвращается как интерфейс `IEnumerator`.

## Как избежать

- использовать дженерики (`List<T>`, `Dictionary<K,V>`) вместо `ArrayList`/`Hashtable`;

    > **Почему:** `ArrayList`/`Hashtable` хранят элементы как `object`. Value-тип (`int`, `struct`) при добавлении
    **боксится** (копируется в кучу), а при чтении — **распаковывается** (каст + копирование обратно). Это лишняя аллокация
    и нагрузка на GC на каждый элемент.

    >
    > ```csharp
    > var list = new ArrayList();
    > list.Add(5);                  // boxing: Add(object)
    > int a = (int)list[0];         // unboxing: индексатор возвращает object
    > var table = new Hashtable();
    > table.Add(1, 10);             // boxing ключа и значения
    > int v = (int)table[1];        // boxing ключа при поиске + unboxing значения
    > ```
    >
    > `List<T>` — дженерик-аналог `ArrayList`, `Dictionary<K,V>` — аналог `Hashtable`. Для value-типов дженерик-коллекции
    работают быстрее: для каждого value-типа рантайм создаёт специализацию типа с подставленным аргументом (`List<int>`
    хранит `int[]`, метод — `Add(int)`), поэтому значение не приводится к `object` и не боксится.
    >
    > ```csharp
    > var list = new List<int>();
    > list.Add(5);                  // без boxing: Add(int)
    > int a = list[0];              // без unboxing: индексатор возвращает int
    > var dict = new Dictionary<int, int>();
    > dict.Add(1, 10);              // без boxing: Add(int, int)
    > int v = dict[1];              // без boxing ключа и без приведения типа
    > ```

- передавать `struct` через дженерик-параметр или `in`, а не через `object`;

    > ```csharp
    > public interface IDamage { float Amount { get; } }
    >
    > public readonly struct HitData : IDamage
    > {
    >     public readonly Vector3 Point;
    >     public readonly Vector3 Normal;
    >     public readonly float Damage;
    >     public float Amount => Damage;
    >     public HitData(Vector3 p, Vector3 n, float d) { Point = p; Normal = n; Damage = d; }
    > }
    >
    > void ApplyObject(object data) => _health -= ((HitData)data).Damage;              // boxing при вызове, unboxing внутри
    > void ApplyInterface(IDamage data) => _health -= data.Amount;                      // boxing при вызове
    > void ApplyGeneric<T>(T data) where T : struct, IDamage => _health -= data.Amount; // без boxing, копия struct
    > void ApplyIn(in HitData data) => _health -= data.Damage;                          // без boxing, передаётся ссылка
    > ```
    >
    > | Параметр | Boxing | Копирование struct (28 байт) |
    > |---|---|---|
    > | `object`, `IDamage` | да, аллокация в куче | да: в кучу |
    > | `T where T : struct, IDamage` | нет | да: на стек |
    > | `in HitData` | нет | нет: передаётся адрес |
    >
    > - `in` + не-`readonly` struct: при вызове метода или свойства компилятор создаёт **defensive copy**, т.к. не может
    гарантировать, что метод не изменит struct. Чтение поля копию не создаёт. Поэтому для `in` struct объявляют `readonly struct`.
    > - Дженерик не убирает boxing, если внутри значение приводится к `object`: `Debug.Log(data)` в `ApplyGeneric<T>` боксит.
    > - `in` выгоден для больших struct (`Matrix4x4` — 64 байта). Для `int`/`float` выигрыша нет: адрес на 64-bit — 8 байт,
    значение — 4.

- осторожно с интерфейсами на `struct` — вызов через интерфейс боксит экземпляр;

    > **Исключение — generic-ограничение.** Если метод параметризован `where T : IInterface`, то вызов `value.Method()` **не боксит**: компилятор знает конкретный тип `T` на этапе JIT и вызывает метод напрямую (девиртуализация через constrained-вызов IL). Бокс возникает только когда struct приводится к **самому типу интерфейса** (`IInterface x = myStruct;`).
    >
    > ```csharp
    > void Call<T>(T x) where T : IComparable<T> => x.CompareTo(x); // T = int → без бокса
    > void Call(IComparable x)                    => x.CompareTo(x); // int боксится в IComparable
    > ```
    >
    > Частый уточняющий вопрос на собесе: почему `List<int>.Sort()` и `EqualityComparer<T>.Default` не аллоцируют на value-типах — именно из-за дженерик-ограничений.

- для строк — `StringBuilder` либо обновлять текст только при изменении.

## Что спрашивают на собеседовании

- Что такое boxing и unboxing; почему boxing — это аллокация в куче.
- Где boxing возникает неявно: не-дженерик коллекции, передача struct как `object`/интерфейса, `string.Format` и интерполяция, `foreach` через интерфейс.
- Почему вызов метода struct через интерфейс боксит, а через generic-ограничение `where T : IInterface` — нет.
- Как избежать boxing (дженерики, `IEquatable<T>`, обновление текста только при изменении).

---