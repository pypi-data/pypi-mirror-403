# AEP API Documentation

**Total Endpoints**: 6

---

## 1. POST /api/v1/aep/

**Summary:** Create Policy

**Operation ID:** `create_policy_api_v1_aep__post`

### Request Body

**Status:** Required

---

## 2. GET /api/v1/aep/

**Summary:** List Policies

**Operation ID:** `list_policies_api_v1_aep__get`

### Parameters

- **sensitivity** (query, Optional)
- **functional_group** (query, Optional)
- **organization_id** (query, Optional)

---

## 3. GET /api/v1/aep/{policy_id}

**Summary:** Get Policy

**Operation ID:** `get_policy_api_v1_aep__policy_id__get`

### Parameters

- **policy_id** (path, Required) - Type: string

---

## 4. PUT /api/v1/aep/{policy_id}

**Summary:** Update Policy

**Operation ID:** `update_policy_api_v1_aep__policy_id__put`

### Parameters

- **policy_id** (path, Required) - Type: string

### Request Body

**Status:** Required

---

## 5. DELETE /api/v1/aep/{policy_id}

**Summary:** Delete Policy

**Operation ID:** `delete_policy_api_v1_aep__policy_id__delete`

### Parameters

- **policy_id** (path, Required) - Type: string

---

## 6. POST /api/v1/aep/validate-connection

**Summary:** Validate Connection

**Operation ID:** `validate_connection_api_v1_aep_validate_connection_post`

### Parameters

- **source_policy_id** (query, Required) - Type: string
- **target_policy_id** (query, Required) - Type: string
- **connection_type** (query, Optional) - Type: string

---

