# APPS API Documentation

**Total Endpoints**: 5

---

## 1. POST /api/v1/apps/

**Summary:** Create App

**Operation ID:** `create_app_api_v1_apps__post`

### Parameters

- **name** (query, Required) - Type: string

### Request Body

**Status:** Required

---

## 2. GET /api/v1/apps/

**Summary:** List Apps

**Operation ID:** `list_apps_api_v1_apps__get`

---

## 3. GET /api/v1/apps/{app_id}

**Summary:** Get App

**Operation ID:** `get_app_api_v1_apps__app_id__get`

### Parameters

- **app_id** (path, Required) - Type: string

---

## 4. PUT /api/v1/apps/{app_id}

**Summary:** Update App

**Operation ID:** `update_app_api_v1_apps__app_id__put`

### Parameters

- **app_id** (path, Required) - Type: string
- **name** (query, Optional)

### Request Body

**Status:** Optional

---

## 5. DELETE /api/v1/apps/{app_id}

**Summary:** Delete App

**Operation ID:** `delete_app_api_v1_apps__app_id__delete`

### Parameters

- **app_id** (path, Required) - Type: string

---

