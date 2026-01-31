# BLUEPRINTS API Documentation

**Total Endpoints**: 12

---

## 1. POST /api/v1/blueprints/blueprints

**Summary:** Create Blueprint

**Operation ID:** `create_blueprint_api_v1_blueprints_blueprints_post`

### Parameters

- **organization_id** (query, Required) - Type: string

### Request Body

**Status:** Required

---

## 2. GET /api/v1/blueprints/blueprints

**Summary:** List Blueprints

**Operation ID:** `list_blueprints_api_v1_blueprints_blueprints_get`

### Parameters

- **user_organization_id** (query, Optional)
- **orchestration_type** (query, Optional)
- **status** (query, Optional)
- **category** (query, Optional)
- **tags** (query, Optional)
- **owner_id** (query, Optional)
- **organization_id** (query, Optional)
- **share_type** (query, Optional)
- **search** (query, Optional)
- **is_template** (query, Optional)
- **sort_by** (query, Optional)
- **page** (query, Optional) - Type: integer
- **page_size** (query, Optional) - Type: integer
- **x-api-key** (header, Optional)

---

## 3. POST /api/v1/blueprints/blueprints/clone

**Summary:** Clone Blueprint

**Operation ID:** `clone_blueprint_api_v1_blueprints_blueprints_clone_post`

### Parameters

- **organization_id** (query, Required) - Type: string

### Request Body

**Status:** Required

---

## 4. GET /api/v1/blueprints/blueprints/{blueprint_id}

**Summary:** Get Blueprint

**Operation ID:** `get_blueprint_api_v1_blueprints_blueprints__blueprint_id__get`

### Parameters

- **blueprint_id** (path, Required) - Type: string
- **organization_id** (query, Optional)
- **x-api-key** (header, Optional)

---

## 5. PUT /api/v1/blueprints/blueprints/{blueprint_id}

**Summary:** Update Blueprint

**Operation ID:** `update_blueprint_api_v1_blueprints_blueprints__blueprint_id__put`

### Parameters

- **blueprint_id** (path, Required) - Type: string
- **organization_id** (query, Required) - Type: string

### Request Body

**Status:** Required

---

## 6. DELETE /api/v1/blueprints/blueprints/{blueprint_id}

**Summary:** Delete Blueprint

**Operation ID:** `delete_blueprint_api_v1_blueprints_blueprints__blueprint_id__delete`

### Parameters

- **blueprint_id** (path, Required) - Type: string
- **organization_id** (query, Required) - Type: string

---

## 7. POST /api/v1/blueprints/blueprints/{blueprint_id}/share

**Summary:** Share Blueprint

**Operation ID:** `share_blueprint_api_v1_blueprints_blueprints__blueprint_id__share_post`

### Parameters

- **blueprint_id** (path, Required) - Type: string
- **organization_id** (query, Required) - Type: string

### Request Body

**Status:** Required

---

## 8. POST /api/v1/blueprints/blueprints/{blueprint_id}/duplicate

**Summary:** Duplicate Blueprint

**Operation ID:** `duplicate_blueprint_api_v1_blueprints_blueprints__blueprint_id__duplicate_post`

### Parameters

- **blueprint_id** (path, Required) - Type: string
- **organization_id** (query, Required) - Type: string

### Request Body

**Status:** Required

---

## 9. POST /api/v1/blueprints/blueprints/{blueprint_id}/use

**Summary:** Use Blueprint

**Operation ID:** `use_blueprint_api_v1_blueprints_blueprints__blueprint_id__use_post`

### Parameters

- **blueprint_id** (path, Required) - Type: string
- **organization_id** (query, Required) - Type: string
- **event_type** (query, Optional) - Type: string

---

## 10. GET /api/v1/blueprints/blueprints/public/{blueprint_id}

**Summary:** Get Public Blueprint

**Operation ID:** `get_public_blueprint_api_v1_blueprints_blueprints_public__blueprint_id__get`

### Parameters

- **blueprint_id** (path, Required) - Type: string

---

## 11. GET /api/v1/blueprints/blueprints/shared/with-me

**Summary:** Get Shared Blueprints

**Operation ID:** `get_shared_blueprints_api_v1_blueprints_blueprints_shared_with_me_get`

### Parameters

- **organization_id** (query, Required) - Type: string
- **page** (query, Optional) - Type: integer
- **page_size** (query, Optional) - Type: integer

---

## 12. GET /api/v1/blueprints/blueprints/public/browse

**Summary:** Browse Public Blueprints

**Operation ID:** `browse_public_blueprints_api_v1_blueprints_blueprints_public_browse_get`

### Parameters

- **orchestration_type** (query, Optional)
- **category** (query, Optional)
- **tags** (query, Optional)
- **search** (query, Optional)
- **sort_by** (query, Optional)
- **page** (query, Optional) - Type: integer
- **page_size** (query, Optional) - Type: integer
- **organization_id** (query, Optional)
- **x-api-key** (header, Optional)

---

