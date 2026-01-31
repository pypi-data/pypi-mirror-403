# GROUPS API Documentation

**Total Endpoints**: 13

---

## 1. POST /api/v1/groups/

**Summary:** Create Group

**Operation ID:** `create_group_api_v1_groups__post`

### Parameters

- **name** (query, Optional)
- **description** (query, Optional)
- **group_aep_id** (query, Optional)

### Request Body

**Status:** Optional

---

## 2. GET /api/v1/groups/all

**Summary:** Get User Groups

**Operation ID:** `get_user_groups_api_v1_groups_all_get`

---

## 3. GET /api/v1/groups/admin

**Summary:** Get Admin Groups

**Operation ID:** `get_admin_groups_api_v1_groups_admin_get`

---

## 4. GET /api/v1/groups/{group_id}

**Summary:** Get Group

**Operation ID:** `get_group_api_v1_groups__group_id__get`

### Parameters

- **group_id** (path, Required) - Type: string

---

## 5. PUT /api/v1/groups/{group_id}

**Summary:** Update Group

**Operation ID:** `update_group_api_v1_groups__group_id__put`

### Parameters

- **group_id** (path, Required) - Type: string

### Request Body

**Status:** Required

---

## 6. DELETE /api/v1/groups/{group_id}

**Summary:** Delete Group

**Operation ID:** `delete_group_api_v1_groups__group_id__delete`

### Parameters

- **group_id** (path, Required) - Type: string

---

## 7. POST /api/v1/groups/{group_id}/members

**Summary:** Add User To Group

**Operation ID:** `add_user_to_group_api_v1_groups__group_id__members_post`

### Parameters

- **group_id** (path, Required) - Type: string
- **user_id_to_add** (query, Required) - Type: string
- **role** (query, Optional) - Type: string

---

## 8. GET /api/v1/groups/{group_id}/members

**Summary:** Get Group Members

**Operation ID:** `get_group_members_api_v1_groups__group_id__members_get`

### Parameters

- **group_id** (path, Required) - Type: string

---

## 9. DELETE /api/v1/groups/{group_id}/members/{user_id_to_remove}

**Summary:** Remove User From Group

**Operation ID:** `remove_user_from_group_api_v1_groups__group_id__members__user_id_to_remove__delete`

### Parameters

- **group_id** (path, Required) - Type: string
- **user_id_to_remove** (path, Required) - Type: string

---

## 10. PUT /api/v1/groups/{group_id}/members/{user_id_to_update}/role

**Summary:** Update Member Role

**Operation ID:** `update_member_role_api_v1_groups__group_id__members__user_id_to_update__role_put`

### Parameters

- **group_id** (path, Required) - Type: string
- **user_id_to_update** (path, Required) - Type: string
- **new_role** (query, Required) - Type: string

---

## 11. POST /api/v1/groups/{group_id}/tags

**Summary:** Add Tags To Group

**Operation ID:** `add_tags_to_group_api_v1_groups__group_id__tags_post`

### Parameters

- **group_id** (path, Required) - Type: string

### Request Body

**Status:** Required

---

## 12. DELETE /api/v1/groups/{group_id}/tags

**Summary:** Remove Tags From Group

**Operation ID:** `remove_tags_from_group_api_v1_groups__group_id__tags_delete`

### Parameters

- **group_id** (path, Required) - Type: string

### Request Body

**Status:** Required

---

## 13. PATCH /api/v1/groups/{group_id}/metadata

**Summary:** Update Group Metadata

**Operation ID:** `update_group_metadata_api_v1_groups__group_id__metadata_patch`

### Parameters

- **group_id** (path, Required) - Type: string

### Request Body

**Status:** Required

---

