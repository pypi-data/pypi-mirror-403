# Task Framework UI - Proxy Mode

> **📚 Companion Documentation**  
> This document covers Proxy Mode functionality. For Direct Mode (task server) documentation, see [README.md](./README.md).

## 🎯 Overview

The Task Framework UI supports two operational modes:

1. **Direct Mode** (default): Connect directly to a Task Framework server
2. **Proxy Mode**: Connect to a Task Framework Proxy that manages multiple task servers

This document covers the Proxy Mode enhancements, which add server management, discovery, and proxied request routing capabilities to the UI.

---

## 📋 Table of Contents

- [Mode Switching](#mode-switching)
- [Proxy Mode Features](#proxy-mode-features)
- [Settings Configuration](#settings-configuration)
- [Server Management](#server-management)
- [Proxied Operations](#proxied-operations)
- [Navigation Differences](#navigation-differences)
- [Implementation Phases](#implementation-phases)

---

## 🔄 Mode Switching

### How It Works

The UI determines its operational mode using the following logic:

1. **Check localStorage** for `tf_proxy_mode` setting
2. **Default to Direct Mode** if not set
3. **User can toggle** via Settings page
4. **Page reloads** after mode change to reinitialize UI

### Mode Detection

```javascript
const STORAGE_KEYS = {
  PROXY_MODE: "tf_proxy_mode",  // "true" or "false" (string)
  ADMIN_API_KEY: "tf_admin_api_key",  // For proxy admin operations
  SELECTED_SERVER: "tf_selected_server",  // Currently selected server ID in proxy mode
  // ... existing keys
};

function isProxyMode() {
  return localStorage.getItem(STORAGE_KEYS.PROXY_MODE) === "true";
}
```

### Mode Toggle Flow

```
User opens Settings page
  ↓
Sees "Proxy Mode" toggle switch
  ↓
Toggles ON → localStorage.setItem("tf_proxy_mode", "true")
  ↓
Page reloads → window.location.reload()
  ↓
All pages check isProxyMode() and adapt UI accordingly
```

---

## ✨ Proxy Mode Features

### Server Management (`/ui/servers`)

**New page for managing enrolled task servers**

Features:
- **List servers** with real-time health status
- **Enroll new servers** via dedicated form
- **Update server configuration** (base_url, weight, max_concurrent, etc.)
- **Delete servers** with confirmation
- **View server details**: task types, metadata, last checked timestamp
- **Manual health check** trigger

### Server Discovery (`GET /servers`)

**Public endpoint for discovering available servers**

- UI automatically fetches server list on proxy mode activation
- Displays server capabilities (task_types, metadata)
- Shows health status and last checked timestamp
- Used to populate server selection dropdown

### Proxied Request Routing

**Path-prefix routing method**: `/servers/{server_id}/{rest_of_path}`

Example:
```javascript
// Proxy mode: GET /servers/thread-server-1/threads
// Direct mode: GET /threads

const baseUrl = isProxyMode() 
  ? `/servers/${selectedServerId}`
  : '';

fetch(`${baseUrl}/threads`, { headers: authHeaders });
```

---

## ⚙️ Settings Configuration

### Proxy Mode Settings Section

**New settings fields in `/ui/settings`:**

| Setting | Key | Description | Required |
|---------|-----|-------------|----------|
| **Proxy Mode** | `tf_proxy_mode` | Enable/disable proxy mode | Yes (default: false) |
| **Admin API Key** | `tf_admin_api_key` | Key for proxy admin operations (server management) | Yes (in proxy mode) |
| **Selected Server** | `tf_selected_server` | Currently selected server ID | No (auto-selected) |

### Settings Page UI Changes

```html
<!-- Existing settings (shown in both modes) -->
<div class="form-group">
  <label>API Key</label>
  <input id="api-key" type="password" />
</div>

<!-- NEW: Proxy Mode Toggle -->
<div class="form-group">
  <label class="flex items-center">
    <input id="proxy-mode-toggle" type="checkbox" class="mr-2" />
    <span>Proxy Mode</span>
  </label>
  <p class="text-sm text-gray-500 mt-1">
    Connect to Task Framework Proxy instead of direct task server
  </p>
</div>

<!-- NEW: Proxy Admin Key (visible only when proxy mode enabled) -->
<div id="admin-key-section" class="form-group" style="display: none;">
  <label>Admin API Key</label>
  <input id="admin-api-key" type="password" />
  <p class="text-sm text-gray-500 mt-1">
    Required for server enrollment and management
  </p>
</div>
```

### Mode Change Behavior

```javascript
document.getElementById("proxy-mode-toggle").addEventListener("change", (e) => {
  const isProxy = e.target.checked;
  
  // Show/hide admin key section
  document.getElementById("admin-key-section").style.display = 
    isProxy ? "block" : "none";
  
  // Save and reload
  localStorage.setItem(STORAGE_KEYS.PROXY_MODE, isProxy.toString());
  
  // Prompt user about reload
  if (confirm("Mode changed. The page will reload to apply changes.")) {
    window.location.reload();
  }
});
```

---

## 🖥️ Server Management

### Server List Page (`/ui/servers`)

**Location**: New page in Proxy Mode only

**Features**:
- Table view of enrolled servers
- Real-time health status polling
- Filter by status (healthy, unhealthy, unknown, draining)
- Sort by name, task types, last checked
- Actions: View, Edit, Delete, Manual Health Check

**Table Columns**:
| Column | Description |
|--------|-------------|
| Server ID | Unique identifier (font-mono) |
| Name | Human-friendly name |
| Status | Health status badge (color-coded) |
| Task Types | Comma-separated list |
| Base URL | Server endpoint |
| Weight | Load balancing weight |
| Max Concurrent | Connection limit |
| Last Checked | Health check timestamp |
| Actions | Icon buttons (view, edit, delete, refresh) |

**Health Status Badges**:
- 🟢 `healthy` - Green badge
- 🔴 `unhealthy` - Red badge
- ⚪ `unknown` - Gray badge
- 🟡 `draining` - Yellow badge

### Server Enrollment Page (`/ui/servers/enroll`)

**Form Fields**:

Required:
- **Server ID**: Unique identifier (alphanumeric, hyphens)
- **Base URL**: HTTP(s) endpoint (e.g., `http://localhost:3001`)
- **Task Types**: Multi-select or comma-separated (e.g., `thread`, `file`)

Optional:
- **Name**: Human-friendly name (default: Server ID)
- **Weight**: Load balancing weight (default: 10, min: 1)
- **Max Concurrent**: Connection limit (default: 100, min: 1)
- **Metadata**: JSON object for custom tags

**Validation**:
- Server ID: Must be unique, alphanumeric with hyphens
- Base URL: Must start with `http://` or `https://`
- Task Types: At least one required
- Weight: Integer >= 1
- Max Concurrent: Integer >= 1
- Metadata: Valid JSON object

### Server Edit Page (`/ui/servers/edit/{server_id}`)

**Same form as enrollment, but:**
- Pre-populate fields from `GET /admin/servers/{server_id}`
- Server ID is read-only (cannot be changed)
- Use `PUT /admin/servers/{server_id}` for updates

### Server Details Page (`/ui/servers/{server_id}`)

**Display**:
- Complete server configuration
- Current health status with refresh button
- Task types list
- Metadata (JSON formatted)
- Recent health check history (if available)
- Actions: Edit, Delete, Manual Health Check

---

## 🔄 Proxied Operations

### Request Routing Logic

All API requests in Proxy Mode are prefixed with `/servers/{server_id}`:

```javascript
function buildApiUrl(endpoint) {
  if (!isProxyMode()) {
    return endpoint;  // Direct mode: /threads
  }
  
  const serverId = localStorage.getItem(STORAGE_KEYS.SELECTED_SERVER);
  if (!serverId) {
    throw new Error("No server selected in proxy mode");
  }
  
  return `/servers/${serverId}${endpoint}`;  // Proxy mode: /servers/thread-server-1/threads
}

// Usage
fetch(buildApiUrl("/threads"), {
  method: "POST",
  headers: authHeaders,
  body: JSON.stringify(threadData),
});
```

### Server Selection Dropdown

**Location**: Sidebar (left menu) in Proxy Mode

**Behavior**:
- Displays at the top of sidebar (below logo/title)
- Lists all healthy servers from `GET /servers`
- Shows server name and health status icon
- Auto-selects first healthy server if none selected
- Persists selection to localStorage (`tf_selected_server`)
- Updates immediately on change (no page reload)

**UI Example**:

```html
<!-- Sidebar component in Proxy Mode -->
<aside class="sidebar">
  <div class="logo-section">
    <h1>Task Framework</h1>
    <span class="badge">Proxy Mode</span>
  </div>
  
  <!-- NEW: Server Selection Dropdown -->
  <div class="server-selector p-4 border-b border-gray-700">
    <label class="text-xs text-gray-400 uppercase mb-2 block">
      Target Server
    </label>
    <select id="server-selector" class="w-full bg-gray-700 text-white rounded px-3 py-2">
      <option value="">-- Select Server --</option>
      <option value="thread-server-1">🟢 Thread Server 1</option>
      <option value="file-server-1">🟢 File Server 1</option>
      <option value="worker-2">🔴 Worker 2 (unhealthy)</option>
    </select>
  </div>
  
  <!-- Existing navigation menu -->
  <nav class="navigation">
    <!-- ... -->
  </nav>
</aside>
```

### Affected Pages

All existing pages work in Proxy Mode with server selection:

| Page | Proxy Mode Behavior |
|------|---------------------|
| **Threads** | Create/list/view threads via selected server |
| **Artifacts** | List/view artifacts via selected server |
| **Webhooks** | Manage webhooks via selected server |
| **Schedules** | Manage schedules via selected server |
| **Files** | Upload/download files via selected server |
| **Metrics** | Show proxy metrics (same `/metrics` endpoint) |
| **Metadata** | **Removed** in proxy mode (no single task metadata) |

---

## 🧭 Navigation Differences

### Direct Mode Navigation

```
Dashboard (Task Server)
├── Threads
├── Artifacts
├── Webhooks
├── Schedules
├── Files
├── Metrics
├── Metadata
└── Settings
```

### Proxy Mode Navigation

```
Dashboard (Proxy)
├── Servers (NEW)
│   ├── List Servers
│   ├── Enroll Server
│   └── Server Details
├── Threads (proxied)
├── Artifacts (proxied)
├── Webhooks (proxied)
├── Schedules (proxied)
├── Files (proxied)
├── Metrics (proxy metrics)
└── Settings (with admin key)
```

### Sidebar Title Changes

```javascript
function updateSidebarTitle() {
  const titleElement = document.getElementById("sidebar-title");
  const modeElement = document.getElementById("sidebar-mode");
  
  if (isProxyMode()) {
    titleElement.textContent = "Task Framework";
    modeElement.textContent = "Proxy Mode";
    modeElement.className = "badge badge-blue";
  } else {
    titleElement.textContent = "Task Framework";
    modeElement.textContent = "Direct Mode";
    modeElement.className = "badge badge-green";
  }
}
```

### Menu Item Visibility

**Hidden in Proxy Mode**:
- Metadata page (no single task metadata in proxy)

**Visible Only in Proxy Mode**:
- Servers management section

**Visible in Both Modes**:
- Dashboard, Threads, Artifacts, Webhooks, Schedules, Files, Metrics, Settings

---

## 🚀 Implementation Phases

### Phase 1: Mode Detection & Settings

**Goal**: Enable proxy mode toggle and persist configuration

**Tasks**:
1. Add `tf_proxy_mode`, `tf_admin_api_key`, `tf_selected_server` to localStorage keys
2. Create `isProxyMode()` utility function
3. Update Settings page with Proxy Mode toggle and Admin API Key field
4. Implement mode change with page reload
5. Update sidebar to show mode badge

**Pages to Modify**:
- `settings.html` - Add proxy mode toggle and admin key field
- `components/sidebar.html` - Add mode badge

**Acceptance Criteria**:
- User can toggle proxy mode in settings
- Admin API key field appears when proxy mode is enabled
- Page reloads after mode change
- Sidebar shows "Proxy Mode" or "Direct Mode" badge

---

### Phase 2: Server Management

**Goal**: Implement full server lifecycle management

**Tasks**:
1. Create `servers.html` - List enrolled servers
2. Create `server-enroll.html` - Enrollment form
3. Create `server-edit.html` - Edit server configuration (reuse enrollment form)
4. Create `server-details.html` - View server details
5. Implement admin API integration:
   - `POST /admin/servers` - Enroll
   - `GET /admin/servers` - List
   - `GET /admin/servers/{id}` - Get details
   - `PUT /admin/servers/{id}` - Update
   - `DELETE /admin/servers/{id}` - Delete
6. Add "Servers" menu item to sidebar (proxy mode only)
7. Implement server health status display with color-coded badges
8. Add manual health check button

**New Files**:
- `pages/servers.html`
- `pages/server-enroll.html`
- `pages/server-details.html`

**Routes to Add** (in `__init__.py`):
- `/ui/servers`
- `/ui/servers/enroll`
- `/ui/servers/edit/{server_id}`
- `/ui/servers/{server_id}`

**Acceptance Criteria**:
- User can list all enrolled servers with health status
- User can enroll new servers with validation
- User can edit server configuration
- User can delete servers with confirmation
- User can view detailed server information
- Admin API key is required and included in requests

---

### Phase 3: Server Discovery & Selection

**Goal**: Implement server discovery and selection dropdown

**Tasks**:
1. Create server discovery function: `GET /servers` (public endpoint)
2. Add server selection dropdown to sidebar (proxy mode only)
3. Populate dropdown from discovery API
4. Persist selected server to localStorage (`tf_selected_server`)
5. Auto-select first healthy server if none selected
6. Show health status icons in dropdown
7. Update selected server on change (no reload)

**Pages to Modify**:
- `components/sidebar.html` - Add server selector dropdown

**Acceptance Criteria**:
- Server dropdown appears in sidebar (proxy mode only)
- Dropdown populated from `GET /servers` endpoint
- Selected server persists to localStorage
- Health status icons displayed in dropdown
- Selection updates immediately without reload

---

### Phase 4: Proxied Requests

**Goal**: Adapt all existing pages to work in proxy mode

**Tasks**:
1. Create `buildApiUrl(endpoint)` utility function
2. Update all API fetch calls to use `buildApiUrl()`
3. Test each page in proxy mode:
   - Threads (list, create, detail, artifacts)
   - Artifacts (list, view, download, archive, delete)
   - Webhooks (list, create, edit, details, deliveries)
   - Schedules (list, create, edit, details, runs)
   - Files (upload, list, download)
4. Add error handling for "no server selected" scenario
5. Hide Metadata menu item in proxy mode

**Pages to Modify**:
- All existing pages with API calls
- `components/sidebar.html` - Hide metadata link in proxy mode

**Acceptance Criteria**:
- All pages work correctly in proxy mode with server selection
- Requests routed via `/servers/{server_id}/...` path prefix
- Error message shown if no server selected
- Metadata menu hidden in proxy mode
- All operations (CRUD) work via proxy

---

### Phase 5: Metrics & Monitoring

**Goal**: Display proxy metrics and verify compatibility

**Tasks**:
1. Test existing `metrics.html` with proxy `/metrics` endpoint
2. Verify Prometheus format compatibility
3. If needed, create separate proxy metrics handling
4. Add proxy-specific metric categories (if different)

**Pages to Modify**:
- `metrics.html` (if format differs)

**Acceptance Criteria**:
- Metrics page works in proxy mode
- Proxy-specific metrics displayed correctly
- No errors when parsing proxy metrics

---

## 📝 API Endpoints Summary

### Admin Endpoints (Proxy Only)

Require `X-Admin-API-Key` header:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/admin/servers` | Enroll new server |
| `GET` | `/admin/servers` | List enrolled servers |
| `GET` | `/admin/servers/{id}` | Get server details |
| `PUT` | `/admin/servers/{id}` | Update server configuration |
| `DELETE` | `/admin/servers/{id}` | Deregister server |

### Discovery Endpoints (Public)

No authentication required:

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/servers` | List servers with health status |
| `GET` | `/openapi.json` | Get OpenAPI spec with proxy routing examples |

### Proxy Health & Metrics

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Proxy health check (returns `"type": "proxy"`) |
| `GET` | `/metrics` | Prometheus metrics (proxy-specific) |

### Proxied Requests

All task server endpoints via path-prefix routing:

```
/servers/{server_id}/{task_server_endpoint}
```

Examples:
- `POST /servers/thread-server-1/threads`
- `GET /servers/thread-server-1/threads/{thread_id}`
- `GET /servers/file-server-1/files/{file_ref}`

---

## 🔍 Testing Checklist

### Mode Switching
- [ ] Toggle proxy mode in settings
- [ ] Admin API key field appears/disappears
- [ ] Page reloads after mode change
- [ ] Mode persists after reload

### Server Management
- [ ] List servers with health status
- [ ] Enroll new server
- [ ] Edit server configuration
- [ ] Delete server with confirmation
- [ ] View server details
- [ ] Manual health check trigger

### Server Selection
- [ ] Dropdown populated from `/servers`
- [ ] Health icons displayed correctly
- [ ] Selection persists to localStorage
- [ ] Auto-select first healthy server

### Proxied Operations
- [ ] Create thread via proxy
- [ ] List threads via proxy
- [ ] Manage artifacts via proxy
- [ ] Manage webhooks via proxy
- [ ] Manage schedules via proxy
- [ ] Upload/download files via proxy

### Error Handling
- [ ] No server selected error
- [ ] Server not found error
- [ ] Upstream timeout error
- [ ] Admin authentication error

---

## 🎨 UI/UX Guidelines

### Proxy Mode Indicators

1. **Sidebar Badge**: Always show mode badge ("Proxy Mode" or "Direct Mode")
2. **Server Selector**: Prominent position in sidebar (proxy mode only)
3. **Health Icons**: Color-coded status indicators (🟢🔴⚪🟡)
4. **Settings Section**: Clear separation between client and admin credentials

### Color Scheme

```css
/* Health Status Colors */
.status-healthy { color: #22c55e; }    /* Green */
.status-unhealthy { color: #ef4444; }  /* Red */
.status-unknown { color: #6b7280; }    /* Gray */
.status-draining { color: #eab308; }   /* Yellow */

/* Mode Badges */
.badge-proxy { background: #3b82f6; }   /* Blue */
.badge-direct { background: #22c55e; }  /* Green */
```

### Responsive Design

- Server selector dropdown: Full width in sidebar
- Server list table: Horizontal scroll on mobile
- Enrollment form: Stacked fields on mobile

---

## 📚 Related Documentation

- [Direct Mode Documentation](./README.md) - Main UI documentation
- [Proxy Architecture](./ARCHITECTURE-PROXY.md) - Technical implementation details
- [Proxy Server Documentation](../../../docs/proxy/README.md) - Proxy server setup and configuration
- [OpenAPI Specification](../../../specs/initial/openapi-enhanced.yaml) - Task Framework API spec
- [Proxy OpenAPI Spec](../../../specs/010-task-proxy/contracts/openapi-proxy.yaml) - Proxy admin API spec

---

## 🤝 Contributing

When adding proxy mode features:

1. **Check mode** using `isProxyMode()` before rendering mode-specific UI
2. **Use `buildApiUrl()`** for all API requests to support both modes
3. **Update both README-PROXY.md and ARCHITECTURE-PROXY.md**
4. **Test in both modes** before submitting changes
5. **Handle errors** for server selection and upstream failures
6. **Follow existing patterns** from Direct Mode implementation

---

**Last Updated**: 2025-11-18  
**Maintainer**: Task Framework Team

