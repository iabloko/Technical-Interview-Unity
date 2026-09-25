[← К содержанию](../README.md)

# Физика в Unity

Unity использует **PhysX** (3D) и Box2D (2D). Физический шаг детерминированно привязан к `FixedUpdate`.

## FixedUpdate и шаг симуляции

Физика обновляется с фиксированным шагом `Time.fixedDeltaTime` (по умолчанию 0.02 с = 50 Гц), независимо от частоты кадров. За один кадр `FixedUpdate` может вызваться 0, 1 или несколько раз. Поэтому:

- Силы и перемещения тел — **в `FixedUpdate`** (`Rigidbody.AddForce`, `MovePosition`).
- Чтение ввода — в `Update` (кадровый), накопить и применить в `FixedUpdate`.
- Перемещение через `transform.position` минует физику и ломает интерполяцию/коллизии.

## Rigidbody и виды тел

- **Dynamic** (`Rigidbody`): управляется физикой, реагирует на силы и столкновения.
- **Kinematic** (`isKinematic = true`): двигается только кодом, не реагирует на силы, но толкает динамические. Двигать через `MovePosition`/`MoveRotation`.
- **Static** (коллайдер без `Rigidbody`): неподвижная геометрия. **Двигать статический коллайдер дорого** — PhysX перестраивает кеш; для движущихся объектов нужен kinematic Rigidbody.

## Коллайдеры, триггеры, слои

- **Collider** — форма для столкновений. Primitive (box/sphere/capsule) дешевле, чем **Mesh Collider** (convex обязателен для динамики).
- **Trigger** (`isTrigger`) — не вызывает физического отклика, только события `OnTriggerEnter/Stay/Exit`.
- Для генерации событий столкновения хотя бы у одного из участников должен быть `Rigidbody`.
- **Layer Collision Matrix** (`Project Settings → Physics`) отключает проверки между ненужными слоями — прямая оптимизация: меньше пар на проверку.

## Continuous Collision Detection (CCD)

Discrete-режим может «протуннелить» быстрый объект сквозь тонкий коллайдер за один шаг. CCD (`Collision Detection: Continuous`) проверяет траекторию между шагами — дороже, включать только для быстрых тел (пули, мячи).

## Raycast и запросы

`Physics.Raycast`, `OverlapSphere`, `SphereCast` и пр.:
- Фильтровать `LayerMask` — не проверять лишние объекты.
- `RaycastNonAlloc` / версии со `Span`/буфером — без аллокации массива результатов (см. [GC](unity-gc.md)).
- `OverlapSphere` без маски по плотной сцене — дорого.

## Что спрашивают на собеседовании

- Почему физика в `FixedUpdate`, а не в `Update`.
- Разница Dynamic / Kinematic / Static и почему нельзя двигать static-коллайдер.
- Когда нужен CCD (туннелирование быстрых объектов).
- Как оптимизировать физику (layer matrix, primitive-коллайдеры, `RaycastNonAlloc`, LayerMask).
- Что нужно для срабатывания `OnTriggerEnter` (Rigidbody + isTrigger).

---