[← К содержанию](../README.md)

# Кастомный рендеринг в URP: Renderer Features, ScriptableRenderPass, Compute Shaders

Как расширять пайплайн [URP](urp-render-pipeline.md) своими проходами рендеринга, не форкая пайплайн целиком.

## Структура кадра URP

**Universal Renderer** (ассет рендерера) выполняет кадр как последовательность проходов: тени → depth prepass (если нужен) → opaque → skybox → transparent → post-processing. Свой код встраивается между ними через **injection points** — `RenderPassEvent`:

`BeforeRenderingShadows → BeforeRenderingPrepasses → BeforeRenderingOpaques → AfterRenderingOpaques → AfterRenderingSkybox → AfterRenderingTransparents → AfterRenderingPostProcessing → AfterRendering`

Выбор точки определяет, что уже доступно (например, `_CameraDepthTexture` и opaque-цвет существуют только после соответствующих проходов) и кого эффект затронет.

## ScriptableRendererFeature + ScriptableRenderPass

Стандартный механизм расширения — пара классов:

- **`ScriptableRendererFeature`** — ассет-обёртка: добавляется в список Renderer Features на Universal Renderer, хранит настройки, создаёт и регистрирует пасс (`AddRenderPasses`). Это конфигурация.
- **`ScriptableRenderPass`** — сам проход: что и когда рисовать. Это исполнение.

```csharp
public class OutlineFeature : ScriptableRendererFeature
{
    [SerializeField] private Material _material;
    private OutlinePass _pass;

    public override void Create() =>
        _pass = new OutlinePass(_material) { renderPassEvent = RenderPassEvent.AfterRenderingOpaques };

    public override void AddRenderPasses(ScriptableRenderer renderer, ref RenderingData data) =>
        renderer.EnqueuePass(_pass);
}
```

Внутри пасса: получить целевые текстуры (**`RTHandle`** — обёртка над RT с автоматическим масштабированием под разрешение камеры), записать команды (drawcalls по фильтру слоёв/LightMode-тегов через `RendererList`, либо fullscreen-блит `Blitter.BlitTexture`).

**Render Graph (Unity 6 / URP 17+):** проходы декларируют входы/выходы (`RecordRenderGraph` вместо `Execute`), граф сам управляет временем жизни промежуточных текстур, отбрасывает неиспользуемые проходы и сливает совместимые (важно для тайловых мобильных GPU — меньше load/store в память). Legacy-путь с `Execute`/`CommandBuffer` — deprecated в новых версиях; на собеседовании стоит знать оба слова.

**Типовые применения:** outline/highlight объектов, кастомный блюр под UI, декали, рендер слоя объектов в отдельную текстуру (миникарта, маска), кастомный пост-процессинг (для простого fullscreen-эффекта есть готовый **Full Screen Pass Renderer Feature** — без кода, только материал).

## Шейдеры в URP: что нужно знать

- Шейдеры пишутся в **HLSL** внутри ShaderLab (`Pass { HLSLPROGRAM ... }`) с библиотекой URP (`Core.hlsl`, `Lighting.hlsl`), либо собираются в **Shader Graph**.
- Built-in шейдеры (`Standard`, surface shaders) **несовместимы** с URP — у URP свои `LightMode`-теги (`UniversalForward`, `ShadowCaster`, `DepthOnly`).
- **Совместимость с SRP Batcher** (см. [батчинг](../06-performance/batching.md)): материальные свойства — в `CBUFFER_START(UnityPerMaterial) ... CBUFFER_END`; несовместимый шейдер выпадает из батчинга всего пайплайна.
- **Варианты**: `#pragma multi_compile` (все комбинации в билд) vs `#pragma shader_feature` (только используемые; недоступные в рантайме через `Material.EnableKeyword` на новых материалах). Взрыв вариантов — главная причина долгих билдов и больших размеров; следить через Shader Variant stripping.
- Доступ к буферам пайплайна: `_CameraDepthTexture`, `_CameraOpaqueTexture` (включаются в настройках URP-ассета) — основа эффектов воды, искажения, soft particles.

## Compute Shaders

**Compute shader** — программа общего назначения на GPU, вне графического конвейера ([вершины/пиксели](graphics-pipeline.md)): без меша и растеризации, читает и пишет произвольные буферы/текстуры. Исполняется **группами потоков**.

```hlsl
#pragma kernel CSMain
RWStructuredBuffer<float3> _Positions;
uint _Count;
float _DeltaTime;

[numthreads(64,1,1)]                      // размер группы: 64 потока
void CSMain (uint3 id : SV_DispatchThreadID)
{
    if (id.x >= _Count) return;           // count не кратен 64 → последняя группа выходит за размер буфера
    _Positions[id.x] += float3(0, -9.8, 0) * _DeltaTime;
}
```

```csharp
var buffer = new ComputeBuffer(count, sizeof(float) * 3);
_shader.SetBuffer(_kernel, "_Positions", buffer);
_shader.SetInt("_Count", count);
_shader.SetFloat("_DeltaTime", Time.deltaTime);
_shader.Dispatch(_kernel, Mathf.CeilToInt(count / 64f), 1, 1);  // число групп
// ...
buffer.Release();   // ComputeBuffer — нативный ресурс, освобождать обязательно
```

- **`numthreads` × Dispatch** = общее число потоков; размер группы подбирают кратным warp/wavefront (32/64).
- Данные: `ComputeBuffer` / `GraphicsBuffer` (`StructuredBuffer` / `RWStructuredBuffer` в HLSL), `RenderTexture` с `enableRandomWrite` (`RWTexture2D`).
- **Чтение результата на CPU**: синхронный `buffer.GetData()` останавливает конвейер (CPU ждёт GPU — stall); правильный путь — **`AsyncGPUReadback`** с готовностью через несколько кадров.
- Лучший паттерн — результат **остаётся на GPU**: compute пишет буфер → им рисуют `Graphics.RenderMeshIndirect` / процедурный шейдер, CPU данные не трогает.
- Применение: GPU-частицы, GPU frustum/occlusion culling, скиннинг, генерация мешей/полей, симуляции (вода, ткань), параллельные вычисления (сортировка, редукция).
- Ограничения: нужна поддержка платформы (`SystemInfo.supportsComputeShaders`; современные мобильные — да, WebGL — нет, WebGPU — да); ветвление внутри warp'а дорого; нет рекурсии.

## Senior-нюансы

- Каждый дополнительный fullscreen-проход на мобильных — это bandwidth: лишний load/store render target на тайловом GPU дороже самой математики. Меньше блитов, объединять эффекты в один проход (см. [мобильная оптимизация](../06-performance/mobile-optimization.md)).
- `RTHandle`/временные RT — через систему пайплайна (`RenderingUtils.ReAllocateIfNeeded` / RenderGraph), а не `new RenderTexture` каждый кадр.
- Кастомный пасс виден во [Frame Debugger](../03-unity-core/frame-debugger.md) — первый инструмент проверки, что пасс встал в нужное место и с нужными целями.
- `CommandBuffer` записывает команды, исполнение — позже на render thread/GPU: состояние (материалы, свойства) фиксировать через `MaterialPropertyBlock`/per-pass материалы, а не менять общий материал между записью и исполнением.

## Что спрашивают на собеседовании

- Как добавить свой проход в URP без модификации пайплайна (Renderer Feature + ScriptableRenderPass, RenderPassEvent).
- Чем `ScriptableRendererFeature` отличается от `ScriptableRenderPass` (конфигурация vs исполнение).
- Что даёт Render Graph (управление ресурсами, merge проходов, выгода для тайловых GPU).
- Почему шейдеры Built-in не работают в URP; что нужно шейдеру для SRP Batcher (`UnityPerMaterial` CBUFFER).
- `multi_compile` vs `shader_feature` и проблема взрыва вариантов.
- Что такое compute shader, как связаны `numthreads` и `Dispatch`.
- Почему `GetData()` после Dispatch — плохо и что вместо (AsyncGPUReadback или данные остаются на GPU + indirect rendering).
- Сценарии compute: GPU-частицы, culling, симуляции.

---