# Task Framework UI - Proxy Mode Architecture

> **🏗️ Technical Documentation for AI Agents & Developers**  
> This document provides complete technical details for implementing Proxy Mode in the Task Framework UI. For user-facing documentation, see [README-PROXY.md](./README-PROXY.md).

> **⚠️ CRITICAL DOCUMENTATION RULE**  
> When you add, modify, or remove proxy-related features, pages, components, or routes:
>
> 1. **ALWAYS UPDATE THIS FILE** (ARCHITECTURE-PROXY.md) with technical details
> 2. **ALWAYS UPDATE README-PROXY.md** with user-facing documentation
> 3. **REFERENCE DIRECT MODE** documentation ([ARCHITECTURE.md](./ARCHITECTURE.md)) when inheriting patterns
>
> This is **NOT OPTIONAL**. Both files must stay in sync for the codebase to remain maintainable.

---

## 📐 Architecture Overview

### Dual-Mode Architecture

The Task Framework UI operates in one of two mutually exclusive modes:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Task Framework UI                            │
│                                                                 │
│  ┌───────────────────────┐      ┌──────────────────────────┐   │
│  │   Direct Mode         │      │    Proxy Mode            │   │
│  │                       │      │                          │   │
│  │  API: /threads        │      │  API: /servers/{id}/... │   │
│  │  Auth: X-API-Key      │      │  Auth: X-API-Key +      │   │
│  │  Target: Single Task  │      │        X-Admin-API-Key  │   │
│  │          Server       │      │  Target: Proxy Server   │   │
│  └───────────┬───────────┘      └────────────┬─────────────┘   │
│              │                               │                 │
│              │   Mode Toggle (Settings)      │                 │
│              └───────────┬───────────────────┘                 │
│                          │                                     │
│              localStorage: tf_proxy_mode                       │
└─────────────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
        ▼                                   ▼
┌───────────────┐                  ┌──────────────────┐
│  Task Server  │                  │  Proxy Server    │
│  (Direct)     │                  │  ┌─────────────┐ │
│               │                  │  │ Server      │ │
│  /threads     │                  │  │ Registry    │ │
│  /artifacts   │                  │  └─────┬───────┘ │
│  /webhooks    │                  │        │         │
│  /schedules   │                  │        ▼         │
│  /files       │                  │  ┌─────────────┐ │
└───────────────┘                  │  │ Load        │ │
                                   │  │ Balancer    │ │
                                   │  └─────┬───────┘ │
                                   │        │         │
                                   └────────┼─────────┘
                                            │
                              ┌─────────────┴─────────────┐
                              │                           │
                              ▼                           ▼
                      ┌──────────────┐           ┌──────────────┐
                      │ Task Server  │           │ Task Server  │
                      │     #1       │           │     #2       │
                      └──────────────┘           └──────────────┘
```

---

## 💾 State Management

### localStorage Schema

```javascript
const STORAGE_KEYS = {
  // Direct Mode Keys (inherited from ARCHITECTURE.md)
  API_KEY: "tf_api_key", // Client API key for task operations
  APP_ID: "tf_app_id", // Optional app identifier
  USER_ID: "tf_user_id", // Optional user identifier

  // Proxy Mode Keys (NEW)
  PROXY_MODE: "tf_proxy_mode", // "true" | "false" (string boolean)
  ADMIN_API_KEY: "tf_admin_api_key", // Admin key for server management
  SELECTED_SERVER: "tf_selected_server", // Currently selected server ID
};
```

### State Persistence

All mode-related state persists across page reloads:

1. **Mode selection** (`tf_proxy_mode`) - Persists mode choice
2. **Admin credentials** (`tf_admin_api_key`) - Persists admin access
3. **Server selection** (`tf_selected_server`) - Persists target server

### State Initialization

```javascript
// Initialize on page load (every page)
document.addEventListener("DOMContentLoaded", function () {
  const isProxy = localStorage.getItem(STORAGE_KEYS.PROXY_MODE) === "true";

  // Update UI based on mode
  updateUIForMode(isProxy);

  // In proxy mode, ensure server is selected
  if (isProxy) {
    ensureServerSelected();
  }
});

function updateUIForMode(isProxy) {
  // Update sidebar title/badge
  document.getElementById("mode-badge").textContent = isProxy
    ? "Proxy Mode"
    : "Direct Mode";

  // Show/hide mode-specific elements
  document.querySelectorAll("[data-mode='proxy']").forEach((el) => {
    el.style.display = isProxy ? "block" : "none";
  });

  document.querySelectorAll("[data-mode='direct']").forEach((el) => {
    el.style.display = isProxy ? "none" : "block";
  });
}

async function ensureServerSelected() {
  let serverId = localStorage.getItem(STORAGE_KEYS.SELECTED_SERVER);

  if (!serverId) {
    // Auto-select first healthy server
    const servers = await fetchServers();
    const healthyServer = servers.find((s) => s.status === "healthy");

    if (healthyServer) {
      serverId = healthyServer.id;
      localStorage.setItem(STORAGE_KEYS.SELECTED_SERVER, serverId);
    }
  }

  return serverId;
}
```

---

## 🌐 API Communication

### Request Building

```javascript
/**
 * Build API URL based on current mode
 *
 * Direct Mode: /threads
 * Proxy Mode: /servers/{server_id}/threads
 */
function buildApiUrl(endpoint) {
  const isProxy = localStorage.getItem(STORAGE_KEYS.PROXY_MODE) === "true";

  if (!isProxy) {
    return endpoint; // Direct mode
  }

  // Proxy mode: prepend server path
  const serverId = localStorage.getItem(STORAGE_KEYS.SELECTED_SERVER);

  if (!serverId) {
    throw new Error(
      "No server selected. Please select a server from the dropdown."
    );
  }

  // Ensure endpoint starts with /
  const normalizedEndpoint = endpoint.startsWith("/")
    ? endpoint
    : `/${endpoint}`;

  return `/servers/${serverId}${normalizedEndpoint}`;
}

/**
 * Build authentication headers based on mode
 */
function buildAuthHeaders() {
  const apiKey = localStorage.getItem(STORAGE_KEYS.API_KEY);
  const appId = localStorage.getItem(STORAGE_KEYS.APP_ID);
  const userId = localStorage.getItem(STORAGE_KEYS.USER_ID);

  const headers = {
    "Content-Type": "application/json",
  };

  if (apiKey) headers["X-API-Key"] = apiKey;
  if (appId) headers["X-App-ID"] = appId;
  if (userId) headers["X-User-ID"] = userId;

  return headers;
}

/**
 * Build admin headers for proxy admin operations
 */
function buildAdminHeaders() {
  const adminKey = localStorage.getItem(STORAGE_KEYS.ADMIN_API_KEY);

  if (!adminKey) {
    throw new Error("Admin API key not configured. Please set it in Settings.");
  }

  return {
    "Content-Type": "application/json",
    "X-Admin-API-Key": adminKey,
  };
}

/**
 * Unified fetch wrapper
 */
async function apiFetch(endpoint, options = {}) {
  const url = buildApiUrl(endpoint);
  const headers = {
    ...buildAuthHeaders(),
    ...options.headers,
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    await handleApiError(response);
  }

  return response;
}

/**
 * Admin API fetch wrapper
 */
async function adminFetch(endpoint, options = {}) {
  // Admin endpoints are NOT proxied - they go directly to proxy
  const headers = {
    ...buildAdminHeaders(),
    ...options.headers,
  };

  const response = await fetch(endpoint, {
    ...options,
    headers,
  });

  if (!response.ok) {
    await handleApiError(response);
  }

  return response;
}

/**
 * Error handler for API responses
 */
async function handleApiError(response) {
  let errorMessage = `HTTP ${response.status}: ${response.statusText}`;

  try {
    const contentType = response.headers.get("content-type");

    // Problem+JSON format (proxy errors)
    if (contentType?.includes("application/problem+json")) {
      const problem = await response.json();
      errorMessage = problem.detail || problem.title || errorMessage;

      // Log additional context
      console.error("API Error (Problem+JSON):", {
        type: problem.type,
        title: problem.title,
        status: problem.status,
        detail: problem.detail,
        code: problem.code,
      });
    }
    // Standard JSON error
    else if (contentType?.includes("application/json")) {
      const error = await response.json();
      errorMessage = error.detail || error.message || errorMessage;
    }
  } catch (e) {
    // Failed to parse error body, use default message
    console.error("Failed to parse error response:", e);
  }

  throw new Error(errorMessage);
}
```

### Usage Examples

```javascript
// Example 1: List threads (works in both modes)
async function loadThreads() {
  try {
    const response = await apiFetch("/threads?limit=50");
    const data = await response.json();
    displayThreads(data.items);
  } catch (error) {
    showError(error.message);
  }
}

// Example 2: Enroll server (proxy mode only, admin endpoint)
async function enrollServer(serverData) {
  try {
    const response = await adminFetch("/admin/servers", {
      method: "POST",
      body: JSON.stringify(serverData),
    });
    const server = await response.json();
    return server;
  } catch (error) {
    showError(error.message);
  }
}

// Example 3: Discover servers (public endpoint, no auth)
async function fetchServers() {
  try {
    const response = await fetch("/servers");
    const data = await response.json();
    return data.servers;
  } catch (error) {
    console.error("Failed to fetch servers:", error);
    return [];
  }
}
```

---

## 🧩 Component Architecture

### Server Selector Component

**Location**: `components/sidebar.html` (proxy mode only)

**Integration**:

```html
<!-- In sidebar.html, add after logo section -->
<div
  data-mode="proxy"
  class="server-selector-container border-b border-gray-700 pb-4 mb-4"
  style="display: none;"
>
  <label
    class="block text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2"
  >
    Target Server
  </label>
  <select
    id="server-selector"
    class="w-full bg-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
  >
    <option value="">-- Select Server --</option>
  </select>
  <div
    id="server-selector-error"
    class="text-red-400 text-xs mt-1"
    style="display: none;"
  >
    No servers available
  </div>
</div>

<script>
  (function () {
    const isProxy = localStorage.getItem("tf_proxy_mode") === "true";

    if (!isProxy) {
      // Hide selector in direct mode
      document.querySelectorAll("[data-mode='proxy']").forEach((el) => {
        el.style.display = "none";
      });
      return;
    }

    // Show selector and populate
    document.querySelectorAll("[data-mode='proxy']").forEach((el) => {
      el.style.display = "block";
    });

    populateServerSelector();

    // Listen for selection changes
    document
      .getElementById("server-selector")
      .addEventListener("change", (e) => {
        const serverId = e.target.value;
        localStorage.setItem("tf_selected_server", serverId);
        console.log("Selected server:", serverId);
      });

    async function populateServerSelector() {
      try {
        const response = await fetch("/servers");
        const data = await response.json();
        const servers = data.servers || [];

        const selector = document.getElementById("server-selector");
        selector.innerHTML = '<option value="">-- Select Server --</option>';

        if (servers.length === 0) {
          document.getElementById("server-selector-error").style.display =
            "block";
          document.getElementById("server-selector-error").textContent =
            "No servers available";
          return;
        }

        const selectedId = localStorage.getItem("tf_selected_server");
        let hasValidSelection = false;

        servers.forEach((server) => {
          const option = document.createElement("option");
          option.value = server.id;

          // Add health status icon
          const icon = getHealthIcon(server.status);
          option.textContent = `${icon} ${server.name || server.id}`;

          if (server.id === selectedId) {
            option.selected = true;
            hasValidSelection = true;
          }

          selector.appendChild(option);
        });

        // Auto-select first healthy server if no valid selection
        if (!hasValidSelection) {
          const healthyServer = servers.find((s) => s.status === "healthy");
          if (healthyServer) {
            selector.value = healthyServer.id;
            localStorage.setItem("tf_selected_server", healthyServer.id);
          }
        }
      } catch (error) {
        console.error("Failed to fetch servers:", error);
        document.getElementById("server-selector-error").style.display =
          "block";
        document.getElementById("server-selector-error").textContent =
          "Failed to load servers";
      }
    }

    function getHealthIcon(status) {
      const icons = {
        healthy: "🟢",
        unhealthy: "🔴",
        unknown: "⚪",
        draining: "🟡",
      };
      return icons[status] || "⚪";
    }
  })();
</script>
```

---

## 📁 Project Structure

### New Files for Proxy Mode

```
ui/
├── pages/
│   ├── servers.html              # NEW: Server list page
│   ├── server-enroll.html        # NEW: Enroll server form
│   ├── server-details.html       # NEW: Server details view
│   └── [existing pages...]       # Modified for proxy mode
│
├── components/
│   ├── sidebar.html              # MODIFIED: Add server selector
│   └── [existing components...]
│
├── README-PROXY.md               # NEW: User documentation
├── ARCHITECTURE-PROXY.md         # NEW: This file (technical docs)
├── README.md                     # EXISTING: Direct mode docs
└── ARCHITECTURE.md               # EXISTING: Direct mode architecture
```

---

## 🔧 FastAPI Routes (`__init__.py`)

### New Proxy Mode Routes

```python
# Proxy mode server management pages
@router.get("/ui/servers", response_class=FileResponse)
async def ui_servers():
    """Serve the servers list page (proxy mode only)."""
    file_path = UI_DIR / "pages" / "servers.html"
    return FileResponse(file_path, media_type="text/html")

@router.get("/ui/servers/enroll", response_class=FileResponse)
async def ui_server_enroll():
    """Serve the server enrollment form (proxy mode only)."""
    file_path = UI_DIR / "pages" / "server-enroll.html"
    return FileResponse(file_path, media_type="text/html")

@router.get("/ui/servers/edit/{server_id}", response_class=FileResponse)
async def ui_server_edit(server_id: str):
    """Serve the server edit form (proxy mode only).

    Note: This route reuses server-enroll.html but in edit mode.
    The page detects edit mode from URL path.
    """
    file_path = UI_DIR / "pages" / "server-enroll.html"
    return FileResponse(file_path, media_type="text/html")

@router.get("/ui/servers/{server_id}", response_class=FileResponse)
async def ui_server_details(server_id: str):
    """Serve the server details page (proxy mode only)."""
    file_path = UI_DIR / "pages" / "server-details.html"
    return FileResponse(file_path, media_type="text/html")
```

### Updated Routes Table

| Route                                     | File                      | Purpose           | Mode              |
| ----------------------------------------- | ------------------------- | ----------------- | ----------------- |
| **Proxy-Specific Routes (NEW)**           |
| `/ui/servers`                             | `servers.html`            | Server list       | Proxy only        |
| `/ui/servers/enroll`                      | `server-enroll.html`      | Enroll server     | Proxy only        |
| `/ui/servers/edit/{server_id}`            | `server-enroll.html`      | Edit server       | Proxy only        |
| `/ui/servers/{server_id}`                 | `server-details.html`     | Server details    | Proxy only        |
| **Existing Routes (Works in Both Modes)** |
| `/ui`                                     | `index.html`              | Dashboard         | Both              |
| `/ui/settings`                            | `settings.html`           | Settings          | Both              |
| `/ui/metrics`                             | `metrics.html`            | Metrics           | Both              |
| `/ui/metadata`                            | `metadata.html`           | Task metadata     | Direct only       |
| `/ui/threads`                             | `threads.html`            | Thread list       | Both              |
| `/ui/threads/create`                      | `thread-create.html`      | Create thread     | Both              |
| `/ui/threads/{thread_id}`                 | `thread-detail.html`      | Thread details    | Both              |
| `/ui/threads/{thread_id}/artifacts`       | `thread-artifacts.html`   | Thread artifacts  | Both              |
| `/ui/artifacts`                           | `artifacts.html`          | All artifacts     | Both              |
| `/ui/webhooks`                            | `webhooks.html`           | Webhooks list     | Both              |
| `/ui/webhooks/create`                     | `webhook-create.html`     | Create webhook    | Both              |
| `/ui/webhooks/edit/{webhook_id}`          | `webhook-create.html`     | Edit webhook      | Both              |
| `/ui/webhooks/{webhook_id}`               | `webhook-details.html`    | Webhook details   | Both              |
| `/ui/schedules`                           | `schedules.html`          | Schedules list    | Both              |
| `/ui/schedules/create`                    | `schedule-create.html`    | Create schedule   | Both              |
| `/ui/schedules/edit/{schedule_id}`        | `schedule-create.html`    | Edit schedule     | Both              |
| `/ui/schedules/{schedule_id}`             | `schedule-details.html`   | Schedule details  | Both              |
| `/ui/files`                               | `files.html`              | Files list        | Both              |
| `/ui/files/upload`                        | `file-upload.html`        | File upload       | Both              |
| `/ui/components/sidebar.html`             | `components/sidebar.html` | Sidebar component | Both (mode-aware) |

---

## 📊 Page-Specific Details

### servers.html (NEW)

**Purpose**: List all enrolled task servers with health status and management actions

**Unique Features**:

- **Real-time health status**: Poll server health every 30 seconds
- **Health status badges**: Color-coded (green=healthy, red=unhealthy, gray=unknown, yellow=draining)
- **Filtering**: By status, task types
- **Sorting**: By name, status, last checked
- **Actions**: View, Edit, Delete, Manual health check

**API Endpoints**:

- `GET /admin/servers` (list with admin key)
- `DELETE /admin/servers/{id}` (delete)
- `GET /servers` (public discovery for health status)

**Table Columns**:

- Server ID (font-mono, clickable to details)
- Name
- Status (badge with icon)
- Task Types (comma-separated tags)
- Base URL
- Weight
- Max Concurrent
- Last Checked (timestamp)
- Actions (icon buttons)

**JavaScript Functions**:

- `loadServers()` - Fetch and display servers
- `pollServerHealth()` - Poll health status every 30s
- `deleteServer(serverId)` - Delete with confirmation
- `manualHealthCheck(serverId)` - Trigger manual check
- `formatTaskTypes(taskTypes)` - Render task type badges
- `renderHealthBadge(status)` - Render status badge with icon

---

### server-enroll.html (NEW)

**Purpose**: Enroll new servers or edit existing ones (dual-purpose page)

**Unique Features**:

- **Dual-mode form**: Create or edit based on URL
- **Auto-detection**: Detects edit mode from `/ui/servers/edit/{id}` path
- **Field validation**: Client-side validation for all fields
- **Base URL validation**: Must start with `http://` or `https://`
- **Task types**: Multi-select or comma-separated input
- **Metadata editor**: JSON editor for custom metadata

**API Endpoints**:

- `POST /admin/servers` (enroll)
- `PUT /admin/servers/{id}` (update)
- `GET /admin/servers/{id}` (load for editing)

**Form Fields**:
| Field | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| Server ID | text | Yes (create only) | - | Alphanumeric + hyphens, unique |
| Name | text | No | Server ID | Max 100 chars |
| Base URL | url | Yes | - | Must be http:// or https:// |
| Task Types | multi-select | Yes | - | At least one required |
| Weight | number | No | 10 | Integer >= 1 |
| Max Concurrent | number | No | 100 | Integer >= 1 |
| Metadata | textarea (JSON) | No | {} | Valid JSON object |

**JavaScript Functions**:

- `detectMode()` - Determine if create or edit mode
- `loadServerForEdit(serverId)` - Fetch and populate form
- `validateForm()` - Client-side validation
- `saveServer(event)` - Submit (POST or PUT based on mode)
- `validateBaseUrl(url)` - URL format validation
- `validateTaskTypes(types)` - At least one required
- `validateJson(jsonString)` - JSON syntax validation

---

### server-details.html (NEW)

**Purpose**: View complete server configuration and status

**Unique Features**:

- **Configuration display**: All server settings in read-only format
- **Health status**: Current status with last checked timestamp
- **Task types**: Displayed as badges
- **Metadata**: JSON formatted and syntax highlighted
- **Actions**: Edit, Delete, Manual health check
- **Breadcrumb navigation**: Back to servers list

**API Endpoints**:

- `GET /admin/servers/{id}` (get server details)
- `DELETE /admin/servers/{id}` (delete)

**Display Sections**:

1. **Overview**: ID, name, base URL
2. **Configuration**: Weight, max concurrent, task types
3. **Status**: Health status badge, last checked timestamp
4. **Metadata**: JSON formatted with syntax highlighting
5. **Actions**: Edit button, Delete button, Health check button

**JavaScript Functions**:

- `loadServer()` - Fetch server details
- `displayServer(server)` - Render server information
- `deleteServerFromDetails()` - Delete with confirmation
- `manualHealthCheck()` - Trigger health check
- `formatMetadata(metadata)` - JSON syntax highlighting

---

### settings.html (MODIFIED)

**Purpose**: Configure API credentials and mode settings

**New Features for Proxy Mode**:

- **Proxy Mode toggle**: Checkbox to enable/disable proxy mode
- **Admin API Key field**: Visible only when proxy mode is enabled
- **Mode change handler**: Reload page after mode change

**Form Sections**:

1. **Connection Settings** (always visible):

   - API Key (required in both modes)
   - App ID (optional)
   - User ID (optional)

2. **Proxy Mode Settings** (NEW):
   - Proxy Mode toggle (checkbox)
   - Admin API Key (visible only when proxy mode enabled)

**JavaScript Functions** (NEW/MODIFIED):

- `loadSettings()` - Load all settings including proxy mode
- `toggleProxyMode()` - Show/hide admin key field
- `saveSettings()` - Save all settings including proxy mode
- `validateProxySettings()` - Ensure admin key is set if proxy mode

**Modified Behavior**:

```javascript
function saveSettings() {
  const apiKey = document.getElementById("api-key").value;
  const appId = document.getElementById("app-id").value;
  const userId = document.getElementById("user-id").value;
  const proxyMode = document.getElementById("proxy-mode-toggle").checked;
  const adminKey = document.getElementById("admin-api-key").value;

  // Validation: Admin key required if proxy mode
  if (proxyMode && !adminKey) {
    showError("Admin API Key is required for Proxy Mode");
    return;
  }

  // Save to localStorage
  localStorage.setItem(STORAGE_KEYS.API_KEY, apiKey);
  localStorage.setItem(STORAGE_KEYS.APP_ID, appId);
  localStorage.setItem(STORAGE_KEYS.USER_ID, userId);
  localStorage.setItem(STORAGE_KEYS.PROXY_MODE, proxyMode.toString());

  if (proxyMode) {
    localStorage.setItem(STORAGE_KEYS.ADMIN_API_KEY, adminKey);
  } else {
    localStorage.removeItem(STORAGE_KEYS.ADMIN_API_KEY);
    localStorage.removeItem(STORAGE_KEYS.SELECTED_SERVER);
  }

  showSuccess("Settings saved successfully");

  // Reload if mode changed
  const previousMode =
    document.getElementById("proxy-mode-toggle").dataset.previousValue ===
    "true";
  if (previousMode !== proxyMode) {
    setTimeout(() => {
      window.location.reload();
    }, 1000);
  }
}
```

---

### components/sidebar.html (MODIFIED)

**Purpose**: Navigation sidebar with mode-aware rendering

**New Features for Proxy Mode**:

- **Mode badge**: Display "Proxy Mode" or "Direct Mode"
- **Server selector dropdown**: Visible only in proxy mode
- **Conditional menu items**: Show/hide based on mode

**Structure**:

```html
<aside
  class="w-64 bg-gray-800 text-white h-screen overflow-y-auto custom-scrollbar"
>
  <!-- Logo and Mode Badge -->
  <div class="p-4 border-b border-gray-700">
    <h1 class="text-xl font-bold">Task Framework</h1>
    <span id="mode-badge" class="badge badge-blue text-xs mt-1">
      <!-- Dynamically set: "Proxy Mode" or "Direct Mode" -->
    </span>
  </div>

  <!-- Server Selector (Proxy Mode Only) -->
  <div
    data-mode="proxy"
    class="server-selector-container"
    style="display: none;"
  >
    <!-- Server dropdown (see Component Architecture section above) -->
  </div>

  <!-- Navigation Menu -->
  <nav class="p-4">
    <!-- Dashboard (Both Modes) -->
    <a href="/ui" data-nav-item="dashboard"> Dashboard </a>

    <!-- Servers (Proxy Mode Only) -->
    <div data-mode="proxy" style="display: none;">
      <h2 class="section-title">Server Management</h2>
      <a href="/ui/servers" data-nav-item="servers"> Servers </a>
    </div>

    <!-- Task Operations (Both Modes) -->
    <h2 class="section-title">Operations</h2>
    <a href="/ui/threads" data-nav-item="threads"> Threads </a>
    <a href="/ui/artifacts" data-nav-item="artifacts"> Artifacts </a>
    <a href="/ui/webhooks" data-nav-item="webhooks"> Webhooks </a>
    <a href="/ui/schedules" data-nav-item="schedules"> Schedules </a>
    <a href="/ui/files" data-nav-item="files"> Files </a>

    <!-- System (Both Modes) -->
    <h2 class="section-title">System</h2>
    <a href="/ui/metrics" data-nav-item="metrics"> Metrics </a>

    <!-- Metadata (Direct Mode Only) -->
    <a href="/ui/metadata" data-nav-item="metadata" data-mode="direct">
      Metadata
    </a>

    <a href="/ui/settings" data-nav-item="settings"> Settings </a>
  </nav>

  <!-- Health Status (Both Modes) -->
  <div id="health-status-container" class="p-4 border-t border-gray-700">
    <!-- Health status widget (inherited from ARCHITECTURE.md) -->
  </div>
</aside>
```

**Mode-Aware JavaScript**:

```javascript
(function () {
  const isProxy = localStorage.getItem("tf_proxy_mode") === "true";

  // Update mode badge
  const badge = document.getElementById("mode-badge");
  badge.textContent = isProxy ? "Proxy Mode" : "Direct Mode";
  badge.className = isProxy
    ? "badge badge-blue text-xs mt-1"
    : "badge badge-green text-xs mt-1";

  // Show/hide mode-specific elements
  document.querySelectorAll("[data-mode='proxy']").forEach((el) => {
    el.style.display = isProxy ? "block" : "none";
  });

  document.querySelectorAll("[data-mode='direct']").forEach((el) => {
    el.style.display = isProxy ? "none" : "block";
  });

  // Populate server selector if proxy mode
  if (isProxy) {
    populateServerSelector();
  }
})();
```

---

### Existing Pages Modifications

All existing pages (threads, artifacts, webhooks, schedules, files) require minimal changes:

**Required Changes**:

1. Replace direct `fetch(endpoint)` calls with `apiFetch(endpoint)`
2. No UI changes needed - transparent to user
3. Error handling already covers proxy errors (Problem+JSON)

**Example Migration**:

```javascript
// BEFORE (Direct Mode only)
async function loadThreads() {
  const response = await fetch("/threads?limit=50", {
    headers: {
      "X-API-Key": localStorage.getItem("tf_api_key"),
    },
  });
  const data = await response.json();
  displayThreads(data.items);
}

// AFTER (Both Modes)
async function loadThreads() {
  const response = await apiFetch("/threads?limit=50");
  const data = await response.json();
  displayThreads(data.items);
}
```

---

## 🎨 Styling Patterns

### Proxy Mode Color Scheme

```css
/* Mode Badges */
.badge-blue {
  background-color: #3b82f6;
  color: white;
  padding: 2px 8px;
  border-radius: 9999px;
  font-weight: 600;
}

.badge-green {
  background-color: #22c55e;
  color: white;
  padding: 2px 8px;
  border-radius: 9999px;
  font-weight: 600;
}

/* Health Status Badges */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 600;
}

.status-healthy {
  background-color: #dcfce7;
  color: #166534;
}

.status-unhealthy {
  background-color: #fee2e2;
  color: #991b1b;
}

.status-unknown {
  background-color: #f3f4f6;
  color: #4b5563;
}

.status-draining {
  background-color: #fef3c7;
  color: #92400e;
}

/* Server Selector */
.server-selector-container {
  padding: 1rem;
  border-bottom: 1px solid #374151;
}

.server-selector-container label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: #9ca3af;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
}

.server-selector-container select {
  width: 100%;
  background-color: #374151;
  color: white;
  border-radius: 0.5rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  border: none;
  outline: none;
}

.server-selector-container select:focus {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

/* Task Type Badges */
.task-type-badge {
  display: inline-block;
  background-color: #dbeafe;
  color: #1e40af;
  padding: 0.125rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-weight: 500;
  margin-right: 0.25rem;
}
```

---

## 🔄 Data Flow Examples

### Example 1: Mode Switching Flow

```
User navigates to /ui/settings
  ↓
Page loads, reads localStorage.getItem("tf_proxy_mode")
  ↓
Displays current mode state (checkbox checked/unchecked)
  ↓
User toggles Proxy Mode checkbox
  ↓
Admin API Key field appears (if checked) or disappears (if unchecked)
  ↓
User enters Admin API Key (if proxy mode)
  ↓
User clicks "Save Settings"
  ↓
JavaScript saves all settings to localStorage:
  - tf_proxy_mode = "true"
  - tf_admin_api_key = "admin_key_value"
  ↓
Success message: "Settings saved. Page will reload..."
  ↓
window.location.reload()
  ↓
All pages now operate in Proxy Mode
```

---

### Example 2: Server Selection Flow (Proxy Mode)

```
User opens any page in Proxy Mode
  ↓
Sidebar loads via htmx
  ↓
Sidebar JavaScript detects proxy mode (tf_proxy_mode = "true")
  ↓
Server selector dropdown is shown
  ↓
Fetch GET /servers (public discovery endpoint)
  ↓
Populate dropdown with servers:
  - 🟢 Thread Server 1 (healthy)
  - 🟢 File Server 1 (healthy)
  - 🔴 Worker 2 (unhealthy)
  ↓
Check localStorage for tf_selected_server
  ↓
If found and valid → Select it in dropdown
If not found → Auto-select first healthy server
  ↓
User changes selection
  ↓
onChange event → localStorage.setItem("tf_selected_server", newId)
  ↓
All subsequent API calls use new server (no reload needed)
```

---

### Example 3: Proxied Thread Creation Flow

```
User navigates to /ui/threads/create (Proxy Mode)
  ↓
Page loads, detects proxy mode
  ↓
Sidebar shows server selector: "Thread Server 1" selected
  ↓
User fills thread creation form:
  - Mode: sync
  - Inputs: [artifact1, artifact2]
  - Params: {model: "gpt-4"}
  ↓
User clicks "Create Thread"
  ↓
JavaScript calls apiFetch("/threads", {...})
  ↓
apiFetch() calls buildApiUrl("/threads")
  ↓
buildApiUrl() checks:
  - tf_proxy_mode = "true" → Proxy mode
  - tf_selected_server = "thread-server-1" → Use this server
  ↓
Returns: "/servers/thread-server-1/threads"
  ↓
Fetch POST to: /servers/thread-server-1/threads
Headers: X-API-Key, X-User-Id, X-App-Id
Body: {mode: "sync", inputs: [...], params: {...}}
  ↓
Proxy receives request:
  - Extracts server_id = "thread-server-1"
  - Looks up server in registry
  - Forwards to: http://localhost:3001/threads
  ↓
Task server processes request and returns thread
  ↓
Proxy forwards response back to UI
  ↓
UI receives thread data and redirects to /ui/threads/{thread_id}
```

---

### Example 4: Server Enrollment Flow

```
User navigates to /ui/servers/enroll (Proxy Mode)
  ↓
Page loads enrollment form
  ↓
User fills form:
  - Server ID: "worker-3"
  - Base URL: "http://localhost:3003"
  - Task Types: ["thread", "file"]
  - Name: "Worker 3"
  - Weight: 10
  - Max Concurrent: 100
  ↓
User clicks "Enroll Server"
  ↓
JavaScript calls saveServer()
  ↓
Validation:
  ✓ Server ID is alphanumeric + hyphens
  ✓ Base URL starts with http:// or https://
  ✓ At least one task type selected
  ✓ Weight >= 1, Max Concurrent >= 1
  ↓
Call adminFetch("/admin/servers", {method: "POST", body: {...}})
  ↓
adminFetch() builds headers:
  - X-Admin-API-Key: localStorage.getItem("tf_admin_api_key")
  ↓
Fetch POST to /admin/servers (NOT PROXIED - direct to proxy)
  ↓
Proxy validates admin key and enrolls server:
  - Add to registry
  - Save to persistence file
  - Start health checks
  ↓
Proxy returns 201 Created with ServerEntry
  ↓
UI shows success message and redirects to /ui/servers
  ↓
Server list page shows newly enrolled server
```

---

## 🛠️ Development Workflows

### Adding a New Proxy-Only Feature

1. **Create HTML page** in `pages/` (e.g., `new-feature.html`)
2. **Add route** in `__init__.py`:
   ```python
   @router.get("/ui/new-feature", response_class=FileResponse)
   async def ui_new_feature():
       """Serve new feature page (proxy mode only)."""
       file_path = UI_DIR / "pages" / "new-feature.html"
       return FileResponse(file_path, media_type="text/html")
   ```
3. **Add navigation link** in `sidebar.html` with `data-mode="proxy"`:
   ```html
   <a href="/ui/new-feature" data-nav-item="new-feature" data-mode="proxy">
     New Feature
   </a>
   ```
4. **Use admin API** in page JavaScript:
   ```javascript
   async function loadFeatureData() {
     const response = await adminFetch("/admin/some-endpoint");
     const data = await response.json();
     displayData(data);
   }
   ```
5. **Update documentation**:
   - Add feature to `README-PROXY.md` (Features section)
   - Add technical details to `ARCHITECTURE-PROXY.md` (this file)

---

### Adapting Existing Page for Proxy Mode

1. **Replace fetch calls** with `apiFetch()`:

   ```javascript
   // Before
   const response = await fetch("/endpoint", { headers: authHeaders });

   // After
   const response = await apiFetch("/endpoint");
   ```

2. **Test in both modes**:

   - Enable proxy mode, select server, test feature
   - Disable proxy mode, test feature directly

3. **No UI changes needed** (transparent routing)

---

### Testing Proxy Mode Features

1. **Start proxy server**:

   ```bash
   python -m task_framework.proxy
   ```

2. **Enroll test servers**:

   ```bash
   curl -X POST http://localhost:9000/admin/servers \
     -H "X-Admin-API-Key: admin_key" \
     -H "Content-Type: application/json" \
     -d '{
       "id": "test-server-1",
       "base_url": "http://localhost:3001",
       "task_types": ["thread"]
     }'
   ```

3. **Open UI** and enable proxy mode in settings

4. **Select server** from dropdown

5. **Test operations** (create thread, list artifacts, etc.)

6. **Verify requests** are routed via `/servers/{id}/...` path

---

## 🚧 Implementation Checklist

### Phase 1: Mode Detection & Settings ✅ COMPLETED

- [x] Add `PROXY_MODE`, `ADMIN_API_KEY`, `SELECTED_SERVER` to localStorage keys
- [x] Create `isProxyMode()` utility function
- [x] Update `settings.html`:
  - [x] Add Proxy Mode toggle checkbox
  - [x] Add Admin API Key input field (conditional visibility)
  - [x] Implement mode change with page reload
  - [x] Validate admin key when proxy mode enabled
- [x] Update `components/sidebar.html`:
  - [x] Add mode badge display
  - [x] Update badge text/color based on mode
- [x] Update `proxy.py`:
  - [x] Register UI router
  - [x] Exclude `/ui/*` paths from proxy forwarding
- [x] Test mode switching:
  - [x] Toggle enables/disables proxy mode
  - [x] Admin key field shows/hides correctly
  - [x] Page reloads after mode change
  - [x] Mode persists after reload
  - [x] UI accessible at http://localhost:9000/ui/settings
  - [x] Mode badge displays correctly (blue for proxy, green for direct)

---

### Phase 2: Server Management ✅ COMPLETED

- [x] Create `pages/servers.html`:
  - [x] Server list table with health status
  - [x] Real-time health polling (manual refresh button)
  - [x] Status filter dropdown
  - [x] Actions: View, Edit, Delete, Health Check
  - [x] Health status badges with icons
  - [x] Pagination support
  - [x] Empty state and error handling
- [x] Create `pages/server-enroll.html`:
  - [x] Enrollment form with all fields
  - [x] Client-side validation
  - [x] Dual-mode detection (create vs edit)
  - [x] Pre-populate fields for edit mode
  - [x] Task type checkboxes and custom types
  - [x] JSON metadata editor
- [x] Create `pages/server-details.html`:
  - [x] Display complete server configuration
  - [x] Health status section with last checked timestamp
  - [x] Metadata JSON formatting with syntax highlighting
  - [x] Actions: Edit, Delete, Health Check (placeholder)
  - [x] Breadcrumb navigation
- [x] Add routes in `__init__.py`:
  - [x] `/ui/servers`
  - [x] `/ui/servers/enroll`
  - [x] `/ui/servers/edit/{server_id}`
  - [x] `/ui/servers/{server_id}`
- [x] Implement admin API integration:
  - [x] `POST /admin/servers` (enrollment)
  - [x] `GET /admin/servers` (list with pagination)
  - [x] `GET /admin/servers/{id}` (get details)
  - [x] `PUT /admin/servers/{id}` (update)
  - [x] `DELETE /admin/servers/{id}` (delete)
  - [x] X-Admin-API-Key authentication
- [x] Update `components/sidebar.html`:
  - [x] Add "Servers" menu item (proxy mode only with data-mode="proxy")
  - [x] Hide "Metadata" menu in proxy mode (data-mode="direct")
  - [x] Update JavaScript to show/hide mode-specific elements
- [x] Test server management:
  - [x] List servers works (verified - servers displaying correctly)
  - [x] Enroll new server works
  - [x] Edit server works
  - [x] Delete server works
  - [x] Health status updates
  - [x] Admin key required (both X-Admin-API-Key and X-API-Key work)
  - [x] Fixed: API returns array directly, not wrapped in object

---

### Phase 3: Server Discovery & Selection ✅ COMPLETED

- [x] Implement server discovery:
  - [x] Fetch from `GET /servers` (public endpoint, no auth required)
  - [x] Parse server list with health status
- [x] Add server selector to sidebar:
  - [x] Create dropdown component with label and error/info sections
  - [x] Populate from discovery API on load
  - [x] Show health status icons (🟢🔴⚪🟡)
  - [x] Persist selection to localStorage (`tf_selected_server`)
  - [x] Auto-select first healthy server if none selected
  - [x] Display server info (task types) below dropdown
- [x] Update `components/sidebar.html`:
  - [x] Add server selector section (proxy mode only with data-mode="proxy")
  - [x] Implement selection change handler (saves to localStorage)
  - [x] Show error if no servers available
  - [x] Add `populateServerSelector()` function
  - [x] Add `handleServerChange()` function
  - [x] Add `showServerInfo()` function
  - [x] Add `getHealthIcon()` helper function
- [x] Test server selection:
  - [x] Dropdown appears in proxy mode only
  - [x] Populated with servers
  - [x] Icons show correct health status
  - [x] Selection persists across page reloads
  - [x] Auto-selection works (first healthy server)
  - [x] Server info displays below dropdown

---

### Phase 4: Proxied Requests ✅ COMPLETED

- [x] Create request routing utilities:
  - [x] Create `components/api-utils.html` with shared JavaScript utilities
  - [x] `buildApiUrl(endpoint)` function - Builds `/servers/{id}/endpoint` in proxy mode
  - [x] `apiFetch(endpoint, options)` wrapper - Unified fetch with auth headers
  - [x] `adminFetch(endpoint, options)` wrapper - For admin endpoints (not proxied)
  - [x] `buildAuthHeaders()` function - Client API authentication
  - [x] `buildAdminHeaders()` function - Admin API authentication
  - [x] `handleApiError(response)` function - Parse Problem+JSON errors
  - [x] `isProxyMode()` helper - Check current mode
  - [x] Add route in `__init__.py` for `/ui/components/api-utils.html`
- [x] Update all existing pages:
  - [x] `threads.html` - Updated with API utils component and apiFetch()
  - [x] `thread-create.html` - Updated with waitForApiUtils() and apiFetch()
  - [x] `thread-detail.html` - Updated with all proxied API calls
  - [x] `thread-artifacts.html` - Updated with proxied artifacts list
  - [x] `artifacts.html` - Updated (list, download, archive, delete)
  - [x] `webhooks.html` - Updated (list, delete)
  - [x] `webhook-create.html` - Updated (load, create, update)
  - [x] `webhook-details.html` - Updated (view, toggle, regenerate, delete)
  - [x] `components/deliveries-table.html` - Updated (list, view details)
  - [x] `schedules.html` - Updated (list, cancel)
  - [x] `schedule-create.html` - Updated (load, create, update)
  - [x] `schedule-details.html` - Updated (view, toggle state, cancel)
  - [x] `components/runs-table.html` - Updated (list, view details)
  - [x] `files.html` - Updated (list, validate, artifacts, download)
  - [x] `file-upload.html` - Updated (direct upload & presigned URL)
  - [x] `index.html` (dashboard) - Updated (removed duplicate STORAGE_KEYS)
  - [x] `metrics.html` - Updated (removed duplicate STORAGE_KEYS, stays direct)
  - [x] `metadata.html` (direct mode only - hidden in proxy mode)
- [x] Hide metadata page in proxy mode:
  - [x] Updated sidebar navigation (already done in Phase 1)
  - [x] Added `data-mode="direct"` attribute
- [x] Test all pages in proxy mode:
  - [x] Threads CRUD
  - [x] Artifacts management
  - [x] Webhooks management (including deliveries)
  - [x] Schedules management (including runs)
  - [x] File operations (upload & download)
  - [x] Error handling (Problem+JSON parsing)
- [x] Test "no server selected" errors

**Note**: Due to the large number of pages (19 total), we're updating them incrementally. The pattern is:

1. Add API utils component: `<div hx-get="/ui/components/api-utils.html" hx-trigger="load" hx-swap="outerHTML"></div>`
2. Replace `fetch()` calls with `apiFetch()`
3. Remove manual header building (now handled by `apiFetch()`)

---

### Phase 5: Metrics & Monitoring ✅ COMPLETED

- [x] Test `metrics.html` with proxy `/metrics`:
  - [x] Verify Prometheus format compatibility
  - [x] Check if parsing works
- [x] Metrics stay direct (not proxied):
  - [x] In proxy mode, `/metrics` shows proxy metrics
  - [x] In direct mode, `/metrics` shows task server metrics
  - [x] Format is identical (Prometheus standard)
- [x] Test metrics display:
  - [x] Proxy metrics shown correctly
  - [x] No parsing errors
  - [x] Auto-refresh works
  - [x] Fixed duplicate STORAGE_KEYS issue

---

## 📚 Reference Documentation

### Related Files (Direct Mode)

- [README.md](./README.md) - User documentation for Direct Mode
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Technical architecture for Direct Mode
- Inherit patterns from Direct Mode for consistency

### Proxy Server Documentation

- [Proxy Server README](../../../docs/proxy/README.md) - Proxy server setup and configuration
- [Proxy OpenAPI Spec](../../../specs/010-task-proxy/contracts/openapi-proxy.yaml) - Admin API specification
- [Integration Script](../../../examples/verfied/__scenarios/2-tasks-1-proxy/001-scenario-simple.sh) - End-to-end proxy testing

### API Specifications

- [Task Framework OpenAPI](../../../specs/initial/openapi-enhanced.yaml) - Task server API (proxied)
- [Proxy Admin API](../../../specs/010-task-proxy/contracts/openapi-proxy.yaml) - Server management API

---

## ✅ AI Agent Checklist

When working on Proxy Mode features:

1. **Before Adding Features**:

   - [ ] Read this file completely
   - [ ] Review [ARCHITECTURE.md](./ARCHITECTURE.md) for inherited patterns
   - [ ] Check [Proxy Server README](../../../docs/proxy/README.md) for backend API
   - [ ] Review [Proxy OpenAPI Spec](../../../specs/010-task-proxy/contracts/openapi-proxy.yaml)

2. **During Development**:

   - [ ] Use `isProxyMode()` to detect mode
   - [ ] Use `buildApiUrl()` for all API requests
   - [ ] Use `adminFetch()` for admin endpoints
   - [ ] Add `data-mode="proxy"` for proxy-only UI elements
   - [ ] Test in both modes (proxy and direct)
   - [ ] Handle "no server selected" errors
   - [ ] Follow existing styling patterns

3. **After Implementation** (⚠️ CRITICAL):
   - [ ] **UPDATE ARCHITECTURE-PROXY.md** with:
     - [ ] New route in "FastAPI Routes" section
     - [ ] New page in "Project Structure"
     - [ ] New page in "Page-Specific Details" section
     - [ ] New patterns or conventions used
   - [ ] **UPDATE README-PROXY.md** with:
     - [ ] New feature in "Features" section
     - [ ] New page in "Navigation Differences"
     - [ ] User-facing instructions
   - [ ] Check for console errors
   - [ ] Verify mode switching works
   - [ ] Test proxy request routing
   - [ ] Test admin authentication

**DOCUMENTATION IS NOT OPTIONAL**: Future developers and AI agents depend on these files being accurate and up-to-date. Treat documentation updates with the same importance as code changes.

---

**Last Updated**: 2025-11-18  
**Maintainer**: Task Framework Team
