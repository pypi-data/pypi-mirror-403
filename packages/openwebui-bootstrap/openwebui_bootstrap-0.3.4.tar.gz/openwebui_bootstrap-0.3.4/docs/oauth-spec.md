# OAuth Provider Specification

This document specifies the OAuth provider configuration for Open WebUI. While OAuth is not currently implemented in the bootstrap project, this specification documents the required configuration for future implementation.

## Overview

Open WebUI supports multiple OAuth providers for user authentication. Each provider requires specific configuration parameters.

## Supported Providers

### 1. Google OAuth

```yaml
oauth:
  google:
    enable: true
    client_id: "your-client-id.apps.googleusercontent.com"
    client_secret: "your-client-secret"
    scope: "openid email profile"
    redirect_uri: "https://your-webui-domain.com/auth/google/callback"
```

**Required Fields:**
- `client_id`: Google OAuth client ID
- `client_secret`: Google OAuth client secret
- `redirect_uri`: Callback URL registered with Google

### 2. Microsoft OAuth

```yaml
oauth:
  microsoft:
    enable: true
    client_id: "your-client-id"
    client_secret: "your-client-secret"
    tenant_id: "your-tenant-id"
    login_base_url: "https://login.microsoftonline.com"
    picture_url: "https://graph.microsoft.com/v1.0/me/photo/$value"
    scope: "openid email profile"
    redirect_uri: "https://your-webui-domain.com/auth/microsoft/callback"
```

**Required Fields:**
- `client_id`: Microsoft application ID
- `client_secret`: Microsoft application secret
- `tenant_id`: Azure AD tenant ID
- `redirect_uri`: Callback URL registered with Microsoft

### 3. GitHub OAuth

```yaml
oauth:
  github:
    enable: true
    client_id: "your-client-id"
    client_secret: "your-client-secret"
    scope: "user:email"
    redirect_uri: "https://your-webui-domain.com/auth/github/callback"
```

**Required Fields:**
- `client_id`: GitHub OAuth app client ID
- `client_secret`: GitHub OAuth app client secret
- `redirect_uri`: Callback URL registered with GitHub

### 4. Feishu OAuth

```yaml
oauth:
  feishu:
    enable: true
    client_id: "your-client-id"
    client_secret: "your-client-secret"
    scope: "contact:user.base:readonly"
    redirect_uri: "https://your-webui-domain.com/auth/feishu/callback"
```

**Required Fields:**
- `client_id`: Feishu app ID
- `client_secret`: Feishu app secret
- `redirect_uri`: Callback URL registered with Feishu

### 5. OpenID Connect (OIDC)

```yaml
oauth:
  oidc:
    enable: true
    client_id: "your-client-id"
    client_secret: "your-client-secret"
    provider_url: "https://your-oidc-provider.com/.well-known/openid-configuration"
    scopes: "openid email profile"
    redirect_uri: "https://your-webui-domain.com/auth/oidc/callback"
    provider_name: "Your SSO Provider"
    username_claim: "name"
    picture_claim: "picture"
    email_claim: "email"
    groups_claim: "groups"
```

**Required Fields:**
- `client_id`: OIDC client ID
- `provider_url`: OIDC discovery endpoint URL
- `redirect_uri`: Callback URL registered with OIDC provider

## General OAuth Configuration

```yaml
oauth:
  enable_signup: true
  merge_accounts_by_email: false
  enable_role_mapping: false
  enable_group_mapping: false
  enable_group_creation: false
  blocked_groups: []
  roles_claim: "roles"
  allowed_roles: ["user", "admin"]
  admin_roles: ["admin"]
  allowed_domains: ["*"]
  update_picture_on_login: false
```

## Implementation Notes

1. **Security**: Always keep OAuth secrets secure and never commit them to version control
2. **Redirect URIs**: Must match exactly what's registered with the OAuth provider
3. **Scopes**: Use the minimum required scopes for your application
4. **Callback URLs**: Must be HTTPS in production environments
5. **State Management**: Open WebUI handles OAuth state and CSRF protection automatically

## Future Implementation

When OAuth support is added to the bootstrap project, the configuration will be integrated into the main `OpenWebUIConfig` model and will support:
- Automatic database configuration for OAuth providers
- User role mapping based on OAuth claims
- Group synchronization from OAuth providers
- Profile picture synchronization

For now, this specification serves as documentation for manual OAuth configuration in Open WebUI.
