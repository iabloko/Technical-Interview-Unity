[← К содержанию](../README.md)

# Управляемая и неуправляемая память

## Управляемая память (managed)

Память, которой управляет **CLR** через **сборщик мусора (GC)**. Сюда попадают все обычные объекты C# (reference-типы) — они живут в managed heap, а GC сам освобождает их, когда на объект больше нет ссылок.

- Выделение — оператором `new`, освобождение — автоматически (GC).
- Разработчик **не** освобождает память вручную.
- Безопасно: нет «висячих» указателей, двойного освобождения и утечек в классическом C/C++ смысле.

```csharp
var list = new List<int>();   // объект в managed heap
// освобождать вручную не нужно — GC сам соберёт, когда ссылок не останется
```

## Неуправляемая память (unmanaged)

Ресурсы **вне контроля GC**. GC не знает, как их освобождать, поэтому это ответственность разработчика.

Примеры неуправляемых ресурсов:
- хендлы ОС: файлы, сокеты, [мьютексы](glossary.md#мьютекс), оконные дескрипторы;
- нативная память: `Marshal.AllocHGlobal`, указатели в `unsafe`-коде;
- ресурсы из нативных библиотек (P/Invoke, C/C++ DLL);
- в Unity — нативные объекты движка (текстуры, меши, `NativeArray<T>`).

```csharp
IntPtr ptr = Marshal.AllocHGlobal(1024); // выделили неуправляемую память
try { /* работаем */ }
finally { Marshal.FreeHGlobal(ptr); }     // обязаны освободить сами
```

---

## Как освобождать неуправляемые ресурсы

### IDisposable + using
Основной механизм детерминированного освобождения. `using` гарантирует вызов `Dispose()` даже при исключении.

```csharp
public class FileLogger : IDisposable
{
    private readonly FileStream _stream;
    public FileLogger(string path) => _stream = File.OpenWrite(path);

    public void Dispose() => _stream.Dispose();  // освобождаем нативный хендл
}

using (var logger = new FileLogger("log.txt")) { /* ... */ }  // Dispose вызовется автоматически
// или: using var logger = new FileLogger("log.txt");
```

### Финализатор (~destructor)
Подстраховка на случай, если забыли вызвать `Dispose()`. Вызывается GC недетерминированно.

```csharp
~FileLogger() { /* освободить нативные ресурсы */ }
```

- **Минусы:** финализатор замедляет сборку (объект переживает лишний цикл GC, попадает в finalization queue).
- **Правило:** опираться на `IDisposable`/`using`, финализатор — только как страховка для неуправляемых ресурсов.

### Полный Dispose-паттерн

```csharp
public class NativeResource : IDisposable
{
    private bool _disposed;

    public void Dispose()
    {
        Dispose(true);
        GC.SuppressFinalize(this);  // финализатор больше не нужен — убираем из очереди
    }

    protected virtual void Dispose(bool disposing)
    {
        if (_disposed) return;
        if (disposing) { /* освободить управляемые ресурсы */ }
        /* освободить неуправляемые ресурсы */
        _disposed = true;
    }

    ~NativeResource() => Dispose(false);
}
```

---

## В контексте Unity

- Сам движок написан на C++; многие managed-объекты (`Texture`, `Mesh`, `Material`, `GameObject`) — лишь обёртки над **нативными** ресурсами. Поэтому `Destroy(obj)` нужен, чтобы освободить нативную часть — GC её не соберёт.
- `Unity.Collections.NativeArray<T>` и подобные — неуправляемые, требуют `Dispose()` (или `Allocator` с автоосвобождением).
- `UnityEngine.Object` переопределяет `==` так, что «уничтоженный» объект сравнивается с `null`, хотя managed-обёртка ещё жива.

```csharp
var data = new NativeArray<int>(100, Allocator.Persistent);
try { /* работаем */ }
finally { data.Dispose(); }   // иначе — утечка нативной памяти
```

## Что спрашивают на собеседовании

- Чем управляемая память отличается от неуправляемых ресурсов и почему GC не освобождает последние.
- Зачем `IDisposable`/`using`, если есть GC.
- Зачем финализатор, почему он замедляет сборку и что делает `GC.SuppressFinalize`.
- Полный Dispose-паттерн: смысл параметра `disposing`.
- Почему для `Texture`/`Mesh`/`Material` нужен `Destroy`, а для `NativeArray<T>` — `Dispose`.

---