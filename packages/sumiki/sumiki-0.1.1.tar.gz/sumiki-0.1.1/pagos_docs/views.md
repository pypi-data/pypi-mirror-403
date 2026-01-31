# VIEWS API Documentation

**Total Endpoints**: 10

---

## 1. POST /api/v1/views/groups/

**Summary:** Create Group

**Operation ID:** `create_group_api_v1_views_groups__post`

### Request Body

**Status:** Required

---

## 2. GET /api/v1/views/groups/

**Summary:** Get Groups

**Operation ID:** `get_groups_api_v1_views_groups__get`

### Parameters

- **organization_id** (query, Required) - Type: string
- **group_type** (query, Optional) - Type: string

---

## 3. POST /api/v1/views/groups/{group_name}/{group_type}/assets

**Summary:** Add Asset To Group

**Operation ID:** `add_asset_to_group_api_v1_views_groups__group_name___group_type__assets_post`

### Parameters

- **group_name** (path, Required) - Type: string
- **group_type** (path, Required) - Type: string
- **organization_id** (query, Required) - Type: string

### Request Body

**Status:** Required

---

## 4. POST /api/v1/views/groups/{group_name}/{group_type}/assets/batch

**Summary:** Add Assets To Group

**Operation ID:** `add_assets_to_group_api_v1_views_groups__group_name___group_type__assets_batch_post`

### Parameters

- **group_name** (path, Required) - Type: string
- **group_type** (path, Required) - Type: string
- **organization_id** (query, Required) - Type: string

### Request Body

**Status:** Required

---

## 5. GET /api/v1/views/groups/{group_name}/{group_type}

**Summary:** Get Group

**Operation ID:** `get_group_api_v1_views_groups__group_name___group_type__get`

### Parameters

- **group_name** (path, Required) - Type: string
- **group_type** (path, Required) - Type: string
- **organization_id** (query, Required) - Type: string

---

## 6. DELETE /api/v1/views/groups/{group_name}/{group_type}

**Summary:** Delete Group

**Operation ID:** `delete_group_api_v1_views_groups__group_name___group_type__delete`

### Parameters

- **group_name** (path, Required) - Type: string
- **group_type** (path, Required) - Type: string
- **organization_id** (query, Required) - Type: string

---

## 7. DELETE /api/v1/views/groups/{group_name}/{group_type}/assets/{asset_id}

**Summary:** Remove Asset From Group

**Operation ID:** `remove_asset_from_group_api_v1_views_groups__group_name___group_type__assets__asset_id__delete`

### Parameters

- **group_name** (path, Required) - Type: string
- **group_type** (path, Required) - Type: string
- **asset_id** (path, Required) - Type: string
- **organization_id** (query, Required) - Type: string

---

## 8. POST /api/v1/views/groups/{group_name}/{group_type}/assets/batch/remove

**Summary:** Remove Assets From Group

**Operation ID:** `remove_assets_from_group_api_v1_views_groups__group_name___group_type__assets_batch_remove_post`

### Parameters

- **group_name** (path, Required) - Type: string
- **group_type** (path, Required) - Type: string
- **organization_id** (query, Required) - Type: string

### Request Body

**Status:** Required

---

## 9. PUT /api/v1/views/groups/{group_name}/{group_type}/assets/{asset_id}/move

**Summary:** Move Asset Between Groups

**Operation ID:** `move_asset_between_groups_api_v1_views_groups__group_name___group_type__assets__asset_id__move_put`

### Parameters

- **group_name** (path, Required) - Type: string
- **group_type** (path, Required) - Type: string
- **asset_id** (path, Required) - Type: string
- **organization_id** (query, Required) - Type: string

### Request Body

**Status:** Required

---

## 10. PUT /api/v1/views/groups/{group_name}/{group_type}/rename

**Summary:** Rename Group

**Operation ID:** `rename_group_api_v1_views_groups__group_name___group_type__rename_put`

### Parameters

- **group_name** (path, Required) - Type: string
- **group_type** (path, Required) - Type: string
- **organization_id** (query, Required) - Type: string

### Request Body

**Status:** Required

---

