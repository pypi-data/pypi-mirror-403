# POLICIES API Documentation

**Total Endpoints**: 10

---

## 1. POST /api/v1/policies/share-resource

**Summary:** Share Resource

**Operation ID:** `share_resource_api_v1_policies_share_resource_post`

### Request Body

**Status:** Required

---

## 2. POST /api/v1/policies/share-resource/multiple

**Summary:** Share Multiple Resources

**Operation ID:** `share_multiple_resources_api_v1_policies_share_resource_multiple_post`

### Request Body

**Status:** Required

---

## 3. POST /api/v1/policies/unshare-resource

**Summary:** Share Resource

**Operation ID:** `share_resource_api_v1_policies_unshare_resource_post`

### Request Body

**Status:** Required

---

## 4. POST /api/v1/policies/

**Summary:** Create Policy

**Operation ID:** `create_policy_api_v1_policies__post`

### Parameters

- **user_id** (query, Required) - Type: string
- **org_id** (query, Required) - Type: string

### Request Body

**Status:** Optional

---

## 5. GET /api/v1/policies/assigned-permissions

**Summary:** Get Policy

**Operation ID:** `get_policy_api_v1_policies_assigned_permissions_get`

### Parameters

- **organization_id** (query, Required) - Type: string
- **permission_type** (query, Required) - Type: string

---

## 6. GET /api/v1/policies/{policy_id}

**Summary:** Get Policy

**Operation ID:** `get_policy_api_v1_policies__policy_id__get`

### Parameters

- **policy_id** (path, Required) - Type: string

---

## 7. PUT /api/v1/policies/{policy_id}

**Summary:** Update Policy

**Operation ID:** `update_policy_api_v1_policies__policy_id__put`

### Parameters

- **policy_id** (path, Required) - Type: string

### Request Body

**Status:** Required

---

## 8. DELETE /api/v1/policies/{policy_id}

**Summary:** Delete Policy

**Operation ID:** `delete_policy_api_v1_policies__policy_id__delete`

### Parameters

- **policy_id** (path, Required) - Type: string

---

## 9. POST /api/v1/policies/{policy_id}/permissions

**Summary:** Add Permission To Policy

**Operation ID:** `add_permission_to_policy_api_v1_policies__policy_id__permissions_post`

### Parameters

- **policy_id** (path, Required) - Type: string

### Request Body

**Status:** Required

---

## 10. DELETE /api/v1/policies/{policy_id}/permissions/{permission_id}

**Summary:** Remove Permission From Policy

**Operation ID:** `remove_permission_from_policy_api_v1_policies__policy_id__permissions__permission_id__delete`

### Parameters

- **policy_id** (path, Required) - Type: string
- **permission_id** (path, Required) - Type: string

---

