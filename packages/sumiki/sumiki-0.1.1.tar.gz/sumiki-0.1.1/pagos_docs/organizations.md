# ORGANIZATIONS API Documentation

**Total Endpoints**: 18

---

## 1. POST /api/v1/organizations/

**Summary:** Create Organization

**Operation ID:** `create_organization_api_v1_organizations__post`

### Parameters

- **name** (query, Optional)
- **domain** (query, Optional)
- **about_organization** (query, Optional)
- **industry** (query, Optional)

---

## 2. GET /api/v1/organizations/all

**Summary:** Get Organization

**Operation ID:** `get_organization_api_v1_organizations_all_get`

---

## 3. GET /api/v1/organizations/domain-exists

**Summary:** Domain Exists

**Operation ID:** `domain_exists_api_v1_organizations_domain_exists_get`

### Parameters

- **domain** (query, Required) - Type: string

---

## 4. GET /api/v1/organizations/current

**Summary:** Get Organization

**Operation ID:** `get_organization_api_v1_organizations_current_get`

---

## 5. POST /api/v1/organizations/current

**Summary:** Get Organization

**Operation ID:** `get_organization_api_v1_organizations_current_post`

### Parameters

- **organization_id** (query, Required) - Type: string

---

## 6. GET /api/v1/organizations/{organization_id}

**Summary:** Get Organization

**Operation ID:** `get_organization_api_v1_organizations__organization_id__get`

### Parameters

- **organization_id** (path, Required) - Type: string

---

## 7. PUT /api/v1/organizations/{organization_id}

**Summary:** Update Organization

**Operation ID:** `update_organization_api_v1_organizations__organization_id__put`

### Parameters

- **organization_id** (path, Required) - Type: string

### Request Body

**Status:** Required

---

## 8. DELETE /api/v1/organizations/{organization_id}

**Summary:** Delete Organization

**Operation ID:** `delete_organization_api_v1_organizations__organization_id__delete`

### Parameters

- **organization_id** (path, Required) - Type: string

---

## 9. GET /api/v1/organizations/{organization_id}/members

**Summary:** Get Organization Members

**Operation ID:** `get_organization_members_api_v1_organizations__organization_id__members_get`

### Parameters

- **organization_id** (path, Required) - Type: string

---

## 10. POST /api/v1/organizations/{organization_id}/add_user/

**Summary:** Add User To Organization

**Operation ID:** `add_user_to_organization_api_v1_organizations__organization_id__add_user__post`

### Parameters

- **organization_id** (path, Required) - Type: string

### Request Body

**Status:** Required

---

## 11. POST /api/v1/organizations/{organization_id}/add_user_direct/

**Summary:** Add User Direct

**Operation ID:** `add_user_direct_api_v1_organizations__organization_id__add_user_direct__post`

### Parameters

- **organization_id** (path, Required) - Type: string

### Request Body

**Status:** Required

---

## 12. POST /api/v1/organizations/{organization_id}/remove_user/{user_id}

**Summary:** Remove User From Organization

**Operation ID:** `remove_user_from_organization_api_v1_organizations__organization_id__remove_user__user_id__post`

### Parameters

- **organization_id** (path, Required) - Type: string
- **user_id** (path, Required) - Type: string

---

## 13. POST /api/v1/organizations/{organization_id}/create_sub_organization

**Summary:** Create Sub Organization

**Operation ID:** `create_sub_organization_api_v1_organizations__organization_id__create_sub_organization_post`

### Parameters

- **organization_id** (path, Required) - Type: string

### Request Body

**Status:** Required

---

## 14. DELETE /api/v1/organizations/{organization_id}/sub_organization/{sub_org_id}

**Summary:** Delete Sub Organization

**Operation ID:** `delete_sub_organization_api_v1_organizations__organization_id__sub_organization__sub_org_id__delete`

### Parameters

- **organization_id** (path, Required) - Type: string
- **sub_org_id** (path, Required) - Type: string

---

## 15. PUT /api/v1/organizations/{organization_id}/sub_organization/{sub_org_id}

**Summary:** Update Sub Organization

**Operation ID:** `update_sub_organization_api_v1_organizations__organization_id__sub_organization__sub_org_id__put`

### Parameters

- **organization_id** (path, Required) - Type: string
- **sub_org_id** (path, Required) - Type: string

### Request Body

**Status:** Required

---

## 16. PUT /api/v1/organizations/{organization_id}/sub_organization/{sub_org_id}/limit

**Summary:** Adjust Sub Organization Limit

**Operation ID:** `adjust_sub_organization_limit_api_v1_organizations__organization_id__sub_organization__sub_org_id__limit_put`

### Parameters

- **organization_id** (path, Required) - Type: string
- **sub_org_id** (path, Required) - Type: string
- **limit** (query, Required) - Type: number

---

## 17. GET /api/v1/organizations/{organization_id}/sub_organization/{sub_org_id}/limit

**Summary:** Get Sub Organization Limit

**Operation ID:** `get_sub_organization_limit_api_v1_organizations__organization_id__sub_organization__sub_org_id__limit_get`

### Parameters

- **organization_id** (path, Required) - Type: string
- **sub_org_id** (path, Required) - Type: string

---

## 18. GET /api/v1/organizations/{organization_id}/sub_organizations_usage

**Summary:** List Sub Organizations With Usage

**Operation ID:** `list_sub_organizations_with_usage_api_v1_organizations__organization_id__sub_organizations_usage_get`

### Parameters

- **organization_id** (path, Required) - Type: string

---

