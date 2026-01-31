# USAGES API Documentation

**Total Endpoints**: 8

---

## 1. GET /api/v1/usages/current

**Summary:** Get Org Usage

**Operation ID:** `get_org_usage_api_v1_usages_current_get`

---

## 2. POST /api/v1/usages/

**Summary:** Create Usage

**Operation ID:** `create_usage_api_v1_usages__post`

### Request Body

**Status:** Required

---

## 3. GET /api/v1/usages/

**Summary:** List Usages

**Operation ID:** `list_usages_api_v1_usages__get`

### Parameters

- **skip** (query, Optional) - Type: integer
- **limit** (query, Optional) - Type: integer

---

## 4. GET /api/v1/usages/{usage_id}

**Summary:** Get Usage

**Operation ID:** `get_usage_api_v1_usages__usage_id__get`

### Parameters

- **usage_id** (path, Required) - Type: string

---

## 5. PUT /api/v1/usages/{usage_id}

**Summary:** Update Usage

**Operation ID:** `update_usage_api_v1_usages__usage_id__put`

### Parameters

- **usage_id** (path, Required) - Type: string

### Request Body

**Status:** Required

---

## 6. DELETE /api/v1/usages/{usage_id}

**Summary:** Delete Usage

**Operation ID:** `delete_usage_api_v1_usages__usage_id__delete`

### Parameters

- **usage_id** (path, Required) - Type: string

---

## 7. PATCH /api/v1/usages/{usage_id}/deactivate

**Summary:** Deactivate Usage

**Operation ID:** `deactivate_usage_api_v1_usages__usage_id__deactivate_patch`

### Parameters

- **usage_id** (path, Required) - Type: string

---

## 8. POST /api/v1/usages/{organization_id}/deduct/{usage_type}

**Summary:** Deduct Usage

**Operation ID:** `deduct_usage_api_v1_usages__organization_id__deduct__usage_type__post`

### Parameters

- **organization_id** (path, Required) - Type: string
- **usage_type** (path, Required) - Type: string
- **count** (query, Required) - Type: number

---

