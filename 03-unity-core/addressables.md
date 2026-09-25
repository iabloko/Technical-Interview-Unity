[← К содержанию](../README.md)

# Addressables: подробно

Addressables — система адресной загрузки ассетов поверх [AssetBundles](asset-management.md), скрывающая ручное управление бандлами и их зависимостями. Адрес (строка) → асинхронная загрузка независимо от того, где физически лежит ассет (в билде, на CDN).

## Базовый цикл: load → use → release

```csharp
AsyncOperationHandle<GameObject> handle =
    Addressables.LoadAssetAsync<GameObject>("enemy_boss");
await handle.Task;                 // или UniTask
GameObject prefab = handle.Result;
// …
Addressables.Release(handle);      // обязательно
```

- Загрузка **асинхронная** — возвращает `AsyncOperationHandle`.
- `InstantiateAsync` создаёт экземпляр и сам ведёт его учёт; парный `Addressables.ReleaseInstance(go)`.

## Ref-counting (ключевое)

Addressables считают ссылки на каждый ассет/бандл. Загрузка увеличивает счётчик, `Release` — уменьшает. Бандл выгружается из памяти, когда счётчик дошёл до нуля. Выгрузка идёт на уровне **бандла**: ассет с нулевым счётчиком остаётся в памяти, пока используется хотя бы один другой ассет из того же бандла (или пока не отработает `Resources.UnloadUnusedAssets`). Поэтому крупные бандлы со смешанным содержимым задерживают освобождение памяти.

- **Каждому `Load`/`Instantiate` обязан соответствовать `Release`/`ReleaseInstance`.** Пропущенный `Release` = ассет навсегда в памяти (утечка) — частая причина роста памяти (см. [Memory Profiler](memory-profiler.md)).
- Двойной `Release` одного handle — ошибка: если операция уже уничтожена, handle невалиден и Addressables сообщают об ошибке; если нет — счётчик уменьшается за чужую загрузку, и ассет выгружается, пока им ещё пользуются.

## AssetReference

Типизированная ссылка на адресный ассет, назначаемая в Inspector (вместо строкового адреса — безопаснее):

```csharp
[SerializeField] private AssetReferenceGameObject _bossRef;
var handle = _bossRef.LoadAssetAsync();
```

`AssetReferenceT<T>` ограничивает тип; есть `AssetReferenceSprite`, `AssetReferenceGameObject` и т. п.

## Labels и группы

- **Label** — тег на ассетах; можно загрузить все с меткой одним вызовом (`LoadAssetsAsync` по label).
- **Groups** — как ассеты пакуются в бандлы (Packed) и где хранятся (Local / Remote).
- Стратегия упаковки (pack together / separately / by label) влияет на размер и число бандлов.

## Каталог и удалённый контент

- **Catalog** — карта «адрес → расположение». Может обновляться удалённо (`CheckForCatalogUpdates`/`UpdateCatalogs`) → доставка контента без переустановки билда.
- Remote-группы кладутся на CDN; билд содержит только каталог и локальные ассеты.
- `DownloadDependenciesAsync` — преднагрузка удалённых бандлов (прогресс-бар загрузки).

## Сборка и нюансы

- Контент собирается отдельно: **Build → New Build → Default Build Script**; при изменении адресных ассетов нужна пересборка контента (иначе рассинхрон с каталогом). Для обновления remote-контента у уже выпущенного плеера — **Update a Previous Build** с файлом `addressables_content_state.bin` от релизной сборки; New Build формирует новую сборку контента под новый билд плеера.
- В Editor — режим **Use Asset Database** (без сборки, быстро) vs **Use Existing Build** (как в релизе).
- Заменяет `Resources.Load` (тот держит всё до `UnloadUnusedAssets` и раздувает стартовую загрузку) и прямые `[SerializeField]`-ссылки для hot-swappable контента.

## Что спрашивают на собеседовании

- Чем Addressables лучше `Resources`/ручных AssetBundles (ref-counting, зависимости, async, удалённый контент).
- Как работает ref-counting и почему важен `Release` (утечки памяти).
- Что такое `AssetReference`, label, group, catalog.
- Как доставлять контент без обновления билда (remote-группы + catalog update).

---