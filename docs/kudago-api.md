# Kudago API

**База URL:** `https://kudago.com/public-api/v1.4/`

---

## Эндпоинты

### GET /places/ — Список мест

**Параметры:**

| Параметр | Тип | Описание |
|---|---|---|
| `lang` | string | `ru` (по умолч.) / `en` |
| `page` | number | Страница (по умолч. 1) |
| `page_size` | number | До 100 (по умолч. 20) |
| `fields` | string | Поля через запятую: `id,title,slug,address,location,site_url,is_closed,timetable,phone,images,description,body_text,coords,subway,favorites_count,comments_count,categories,tags` |
| `expand` | string | `images` — для картинок с превью |
| `order_by` | string | `-rank,-id` (по умолч.), можно: `id`, `title`, `slug`, `address`, `phone`, `favorites_count` и др. Минус = убывание |
| `text_format` | string | `html` / `plain` / `text` |
| `ids` | number | Фильтр по ID через запятую |
| `location` | string | `spb` / `msk` / `nsk` / `ekb` / `nnv` / `kzn` / `sochi` / `ufa` / `krasnoyarsk` / `vbg` / `smr` / `krd` / `kev` / `new-york` |
| `categories` | string | Фильтр по категориям через запятую, `-cat` = исключить |
| `tags` | string | Фильтр по тегам через запятую |
| `has_showings` | string | Только `movie` |
| `showing_since` / `showing_until` | number/ISO | UNIX timestamp или ISO 8601 (UTC) |
| `is_free` | number | `1` / `0` |
| `lon`, `lat`, `radius` | number | **Только вместе!** Фильтр по радиусу в метрах |
| `parent_id` | number | Дочерние места |

**Ответ:** `{ count, next, previous, results: [...] }`

---

### GET /places/{id}/ — Детализация места

**Параметры:** те же `lang`, `fields`, `expand`

**Поля ответа:** `id`, `title`, `short_title`, `slug`, `address`, `location`, `timetable`, `phone`, `is_stub`, `images`, `description`, `body_text`, `site_url`, `foreign_url`, `coords`, `subway`, `favorites_count`, `comments_count`, `is_closed`, `categories`, `tags`, `age_restriction`, `disable_comments`, `has_parking_lot`

С `expand=images` — картинки с `thumbnails: { "144x96": "...", "640x384": "..." }`

---

### GET /places/{id}/comments/ — Комментарии

**Параметры:** `lang`, `page`, `page_size`, `fields` (`id`, `date_posted`, `text`, `user`, `is_deleted`, `replies_count`, `thread`, `reply_to`), `order_by`, `ids`

**Ответ:** `{ count, next, previous, results: [...] }`

---

## Ошибки

| Код | Описание |
|---|---|
| `400` | Неверный `has_showings`, недопустимая `categories`, неполная тройка `lat/lon/radius` |
| `404` | Нет места с таким id |

---

## Версии API

`v1` / `v1.1` / `v1.2` / `v1.3` / `v1.4`