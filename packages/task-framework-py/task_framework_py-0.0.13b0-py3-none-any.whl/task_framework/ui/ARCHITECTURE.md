# Task Framework UI Architecture

> **For AI Agents & Developers**: This document provides a complete technical overview of the UI architecture, patterns, conventions, and implementation details to help you understand, maintain, and extend this codebase.

> **⚠️ CRITICAL DOCUMENTATION RULE**  
> When you add, modify, or remove any feature, page, component, or route:
>
> 1. **ALWAYS UPDATE THIS FILE** (ARCHITECTURE.md) with technical details
> 2. **ALWAYS UPDATE README.md** with user-facing documentation
>
> This is **NOT OPTIONAL**. Both files must stay in sync for the codebase to remain maintainable.

## 🎯 Quick Context

This is a **component-based web UI** for Task Framework, built with:

- **htmx** for dynamic content loading
- **Tailwind CSS** for styling
- **Vanilla JavaScript** for logic
- **FastAPI** for serving HTML files

**Key Design Principle**: No server-side rendering. The UI consumes the Task Framework REST API via htmx and JavaScript.

---

## 📐 Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Browser                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │            HTML Pages (pages/*.html)                │    │
│  │  ┌──────────────────────────────────────────────┐   │    │
│  │  │  Sidebar Component (components/sidebar.html) │   │    │
│  │  │  (loaded via htmx on every page)             │   │    │
│  │  └──────────────────────────────────────────────┘   │    │
│  │                                                     │    │
│  │  Page-Specific JavaScript (vanilla JS)              │    │
│  │  ↓                                                  │    │
│  │  localStorage (API credentials)                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                           ↕ htmx/fetch                      │
└─────────────────────────────────────────────────────────────┘
                            ↕ HTTP
┌────────────────────────────────────────────────────────────┐
│                      FastAPI Server                        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  UI Routes (__init__.py)                            │   │
│  │  - Serve HTML files                                 │   │
│  │  - No server-side rendering                         │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Task Framework API                                 │   │
│  │  /threads, /health, /artifacts, etc.                │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
ui/
├── __init__.py                 # FastAPI routes (UI entry points)
│
├── pages/                       # Full HTML pages
│   ├── index.html              # Dashboard/Home page
│   ├── settings.html           # Settings page
│   ├── metrics.html            # Metrics dashboard page
│   ├── metadata.html           # Task metadata page
│   ├── threads.html            # Thread list page
│   ├── thread-create.html      # Thread creation form
│   ├── thread-detail.html      # Thread detail view
│   ├── thread-artifacts.html   # Thread-specific artifacts
│   ├── artifacts.html          # All artifacts management page
│   ├── webhooks.html           # Webhooks list page
│   ├── webhook-create.html     # Create/edit webhook form
│   ├── webhook-details.html    # Webhook details and delivery history
│   ├── schedules.html          # Schedules list page
│   ├── schedule-create.html    # Create/edit schedule form
│   ├── schedule-details.html   # Schedule details and run history
│   ├── files.html              # Files list page
│   └── file-upload.html        # File upload page
│
├── components/                  # Reusable HTML components
│   ├── sidebar.html            # Navigation sidebar
│   ├── deliveries-table.html   # Webhook deliveries table
│   └── runs-table.html         # Schedule runs table
│
├── README.md                    # User documentation
└── ARCHITECTURE.md             # This file (AI agent guide)
```

---

## 🧩 Component Architecture

### Sidebar Component Pattern

**Location**: `components/sidebar.html`

**Purpose**: Reusable navigation component loaded on every page via htmx.

**How It Works**:

1. Each page includes a placeholder div with `hx-get="/ui/components/sidebar.html"`
2. htmx loads the sidebar on page load (`hx-trigger="load"`)
3. Sidebar replaces the placeholder (`hx-swap="outerHTML"`)
4. Sidebar's JavaScript auto-executes when loaded

**Key Features**:

- Navigation menu with active state detection
- Connection status indicator (configured/not configured)
- Health status indicator (healthy/unhealthy/error)
- Auto-refresh health status every 30 seconds

**Implementation Pattern**:

```html
<!-- In every page -->
<div hx-get="/ui/components/sidebar.html" hx-trigger="load" hx-swap="outerHTML">
  <!-- Loading placeholder -->
  <aside class="w-64 bg-gray-800 text-white flex items-center justify-center">
    <div class="text-gray-400 text-sm">Loading...</div>
  </aside>
</div>
```

**JavaScript Execution**:

- Wrapped in IIFE `(function() { ... })()`
- Runs immediately when component loads
- Updates nav active state based on URL
- Polls `/health` endpoint every 30s
- Updates connection status from localStorage

### Page Structure Pattern

Every page follows this structure:

```html
<!DOCTYPE html>
<html lang="en" class="h-full">
  <head>
    <meta charset="UTF-8" />
    <title>Page Title - Task Framework</title>

    <!-- Tailwind CSS via CDN -->
    <script src="https://cdn.tailwindcss.com"></script>

    <!-- htmx via CDN -->
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>

    <!-- Custom styles -->
    <style>
      .nav-item {
        transition: all 0.2s ease-in-out;
      }
      .custom-scrollbar::-webkit-scrollbar {
        width: 6px;
      }
      /* Page-specific styles */
    </style>
  </head>
  <body class="h-full bg-gray-50">
    <div class="flex h-screen overflow-hidden">
      <!-- Sidebar component (loaded via htmx) -->
      <div
        hx-get="/ui/components/sidebar.html"
        hx-trigger="load"
        hx-swap="outerHTML"
      >
        <aside
          class="w-64 bg-gray-800 text-white flex items-center justify-center"
        >
          <div class="text-gray-400 text-sm">Loading...</div>
        </aside>
      </div>

      <!-- Main content -->
      <main class="flex-1 overflow-y-auto">
        <!-- Page content here -->
      </main>
    </div>

    <!-- Page-specific JavaScript -->
    <script>
      const STORAGE_KEYS = {
        API_KEY: "tf_api_key",
        APP_ID: "tf_app_id",
        USER_ID: "tf_user_id",
      };

      // Page logic here
    </script>
  </body>
</html>
```

---

## 🔧 FastAPI Routes (`__init__.py`)

### Route Pattern

All routes follow this pattern:

```python
@router.get("/ui/path", response_class=FileResponse)
async def ui_function_name():
    """Docstring describing the page."""
    file_path = UI_DIR / "pages" / "filename.html"
    return FileResponse(file_path, media_type="text/html")
```

### Current Routes

| Route                               | File                      | Purpose                      |
| ----------------------------------- | ------------------------- | ---------------------------- |
| `/ui`                               | `index.html`              | Dashboard/home page          |
| `/ui/settings`                      | `settings.html`           | Settings configuration       |
| `/ui/metrics`                       | `metrics.html`            | Metrics dashboard            |
| `/ui/metadata`                      | `metadata.html`           | Task metadata                |
| `/ui/threads`                       | `threads.html`            | Thread list                  |
| `/ui/threads/create`                | `thread-create.html`      | Create thread form           |
| `/ui/threads/{thread_id}`           | `thread-detail.html`      | Thread details               |
| `/ui/threads/{thread_id}/artifacts` | `thread-artifacts.html`   | Thread-specific artifacts    |
| `/ui/artifacts`                     | `artifacts.html`          | All artifacts management     |
| `/ui/webhooks`                      | `webhooks.html`           | Webhooks list                |
| `/ui/webhooks/create`               | `webhook-create.html`     | Create webhook form          |
| `/ui/webhooks/edit/{webhook_id}`    | `webhook-create.html`     | Edit webhook form            |
| `/ui/webhooks/{webhook_id}`         | `webhook-details.html`    | Webhook details & deliveries |
| `/ui/schedules`                     | `schedules.html`          | Schedules list               |
| `/ui/schedules/create`              | `schedule-create.html`    | Create schedule form         |
| `/ui/schedules/edit/{schedule_id}`  | `schedule-create.html`    | Edit schedule form           |
| `/ui/schedules/{schedule_id}`       | `schedule-details.html`   | Schedule details & runs      |
| `/ui/files`                         | `files.html`              | Files list                   |
| `/ui/files/upload`                  | `file-upload.html`        | File upload page             |
| `/ui/components/sidebar.html`       | `components/sidebar.html` | Sidebar component            |
| `/ui/components/deliveries-table.html` | `components/deliveries-table.html` | Deliveries table component |
| `/ui/components/runs-table.html`    | `components/runs-table.html` | Runs table component      |

### Adding New Routes

1. Create the HTML file in `pages/` or `components/`
2. Add a route in `__init__.py`:

```python
@router.get("/ui/new-page", response_class=FileResponse)
async def ui_new_page():
    """Serve the new page.

    Detailed description of what this page does.
    """
    file_path = UI_DIR / "pages" / "new-page.html"
    return FileResponse(file_path, media_type="text/html")
```

---

## 💾 State Management

### localStorage Keys

```javascript
const STORAGE_KEYS = {
  API_KEY: "tf_api_key", // Required for API authentication
  APP_ID: "tf_app_id", // Optional filter
  USER_ID: "tf_user_id", // Optional filter
};
```

### Reading from localStorage

```javascript
const apiKey = localStorage.getItem(STORAGE_KEYS.API_KEY) || "";
const appId = localStorage.getItem(STORAGE_KEYS.APP_ID) || "";
const userId = localStorage.getItem(STORAGE_KEYS.USER_ID) || "";
```

### Writing to localStorage

```javascript
localStorage.setItem(STORAGE_KEYS.API_KEY, apiKey);
localStorage.setItem(STORAGE_KEYS.APP_ID, appId);
localStorage.setItem(STORAGE_KEYS.USER_ID, userId);
```

### Clearing localStorage

```javascript
localStorage.removeItem(STORAGE_KEYS.API_KEY);
localStorage.removeItem(STORAGE_KEYS.APP_ID);
localStorage.removeItem(STORAGE_KEYS.USER_ID);
```

---

## 🌐 API Communication

### Authentication Headers

All API requests must include headers from localStorage:

```javascript
const headers = {
  "X-API-Key": apiKey,
  ...(appId && { "X-App-ID": appId }),
  ...(userId && { "X-User-ID": userId }),
};
```

### Fetch Pattern

```javascript
async function fetchFromAPI(endpoint, method = "GET", body = null) {
  const apiKey = localStorage.getItem(STORAGE_KEYS.API_KEY);
  const appId = localStorage.getItem(STORAGE_KEYS.APP_ID);
  const userId = localStorage.getItem(STORAGE_KEYS.USER_ID);

  const options = {
    method,
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": apiKey,
      ...(appId && { "X-App-ID": appId }),
      ...(userId && { "X-User-ID": userId }),
    },
  };

  if (body && method !== "GET") {
    options.body = JSON.stringify(body);
  }

  try {
    const response = await fetch(endpoint, options);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`Error fetching ${endpoint}:`, error);
    throw error;
  }
}
```

### htmx Configuration

htmx automatically includes auth headers via event listener:

```javascript
document.body.addEventListener("htmx:configRequest", function (event) {
  const apiKey = localStorage.getItem(STORAGE_KEYS.API_KEY) || "";
  const appId = localStorage.getItem(STORAGE_KEYS.APP_ID) || "";
  const userId = localStorage.getItem(STORAGE_KEYS.USER_ID) || "";

  if (apiKey) event.detail.headers["X-API-Key"] = apiKey;
  if (appId) event.detail.headers["X-App-ID"] = appId;
  if (userId) event.detail.headers["X-User-ID"] = userId;
});
```

---

## 🎨 Styling Patterns

### Tailwind CSS Utilities

#### Layout

```html
<div class="flex items-center justify-between p-4">...</div>
<div class="grid grid-cols-3 gap-4">...</div>
<div class="w-64 h-screen overflow-y-auto">...</div>
```

#### Colors

```html
<!-- Primary (Blue) -->
<button class="bg-blue-600 hover:bg-blue-700 text-white">...</button>

<!-- Success (Green) -->
<span class="text-green-600 bg-green-100">...</span>

<!-- Danger (Red) -->
<div class="bg-red-50 border-red-200 text-red-700">...</div>

<!-- Warning (Yellow) -->
<span class="bg-yellow-100 text-yellow-800">...</span>

<!-- Dark (Gray) -->
<aside class="bg-gray-800 text-white">...</aside>
```

#### State Badges

```html
<span class="state-queued px-2 py-1 text-xs font-semibold text-white rounded">
  queued
</span>
```

```css
.state-queued {
  background-color: #eab308;
}
.state-running {
  background-color: #3b82f6;
}
.state-succeeded {
  background-color: #22c55e;
}
.state-failed {
  background-color: #ef4444;
}
.state-stopped {
  background-color: #6b7280;
}
```

### Custom Styles

```css
/* Navigation item hover effect */
.nav-item {
  transition: all 0.2s ease-in-out;
}
.nav-item:hover {
  transform: translateX(4px);
}

/* Custom scrollbar */
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #1f2937;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: #4b5563;
  border-radius: 3px;
}

/* Fade-in animation */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
.fade-in {
  animation: fadeIn 0.3s ease-out;
}
```

---

## 📋 Common JavaScript Patterns

### Page Initialization

```javascript
document.addEventListener("DOMContentLoaded", function () {
  console.log("Page initialized");

  // Load data
  loadData();

  // Setup event listeners
  document.getElementById("btn-refresh").addEventListener("click", loadData);
});
```

### UI State Management

```javascript
// Show loading state
function showLoading() {
  document.getElementById("loading-state").classList.remove("hidden");
  document.getElementById("error-state").classList.add("hidden");
  document.getElementById("empty-state").classList.add("hidden");
  document.getElementById("content").classList.add("hidden");
}

// Show error state
function showError(message) {
  document.getElementById("loading-state").classList.add("hidden");
  document.getElementById("error-state").classList.remove("hidden");
  document.getElementById("empty-state").classList.add("hidden");
  document.getElementById("content").classList.add("hidden");
  document.getElementById("error-message").textContent = message;
}

// Show empty state
function showEmpty() {
  document.getElementById("loading-state").classList.add("hidden");
  document.getElementById("error-state").classList.add("hidden");
  document.getElementById("empty-state").classList.remove("hidden");
  document.getElementById("content").classList.add("hidden");
}

// Show content
function showContent() {
  document.getElementById("loading-state").classList.add("hidden");
  document.getElementById("error-state").classList.add("hidden");
  document.getElementById("empty-state").classList.add("hidden");
  document.getElementById("content").classList.remove("hidden");
}
```

### Data Formatting

```javascript
// Format date/time
function formatDateTime(dateString) {
  if (!dateString) return "-";
  const date = new Date(dateString);
  return date.toLocaleString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// Format file size
function formatSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + " KB";
  if (bytes < 1024 * 1024 * 1024)
    return (bytes / (1024 * 1024)).toFixed(2) + " MB";
  return (bytes / (1024 * 1024 * 1024)).toFixed(2) + " GB";
}

// Escape HTML
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
```

---

## 🔄 Data Flow Examples

### Example 1: Loading Threads List

```
User → /ui/threads page
    ↓
1. Sidebar loads via htmx
    ↓
2. Page JavaScript initializes
    ↓
3. Read API key from localStorage
    ↓
4. Fetch GET /threads with auth headers
    ↓
5. Render threads table
    ↓
6. User clicks "View" → Navigate to /ui/threads/{id}
```

### Example 2: Creating a Thread

```
User → /ui/threads/create page
    ↓
1. Form displays with default values
    ↓
2. User fills form
    ↓
3. User submits
    ↓
4. JavaScript validates input
    ↓
5. POST /threads with body & auth headers
    ↓
6. On success → Redirect to /ui/threads/{new_id}
    ↓
7. On error → Display error message
```

### Example 3: Health Status Updates

```
Sidebar loads
    ↓
1. Immediately fetch GET /health
    ↓
2. Parse response: { status, database, file_storage, scheduler }
    ↓
3. Update health-status element (healthy/unhealthy)
    ↓
4. Update connection-status from localStorage
    ↓
5. Set interval: repeat every 30 seconds
```

---

## 🛠️ Development Workflows

### Adding a New API Feature

1. **Check OpenAPI Spec**: `specs/initial/openapi-enhanced.yaml`
2. **Create/Update Page**: Add form, display, or action
3. **Implement JavaScript**: Fetch data, validate, submit
4. **Test with Browser DevTools**: Check network, console, localStorage

### Debugging

#### Browser DevTools

- **Console**: Check for JavaScript errors
- **Network**: Inspect API requests/responses
- **Application → localStorage**: View stored credentials
- **Elements**: Inspect DOM and classes

#### Common Issues

- **"Not configured"**: API key not set in localStorage
- **401 Unauthorized**: Invalid API key
- **404 Not Found**: Check route in `__init__.py`
- **Sidebar not loading**: Check `hx-get` URL
- **Health status stuck**: Check `/health` endpoint

### Testing Checklist

When adding new features:

- [ ] Page loads without errors
- [ ] Sidebar loads and displays correctly
- [ ] API authentication works (headers sent)
- [ ] Loading states display properly
- [ ] Error states display properly
- [ ] Empty states display properly
- [ ] Data renders correctly
- [ ] Actions (buttons, links) work
- [ ] Browser console has no errors
- [ ] Responsive design works (desktop, tablet, mobile)

---

## 📊 Page-Specific Details

### index.html (Dashboard)

- **Purpose**: Home page with system health overview
- **Unique Features**:
  - Real-time health status cards (database, storage, scheduler)
  - Auto-refreshing every 30s
- **API Endpoints**: `/health`

### settings.html

- **Purpose**: Configure API credentials
- **Unique Features**:
  - localStorage read/write
  - Show/hide API key toggle
  - Form validation
- **API Endpoints**: None (localStorage only)

### metrics.html

- **Purpose**: Display Prometheus metrics in human-readable format
- **Unique Features**:
  - **Prometheus Parser**: Parses text-based Prometheus metrics format into structured data
  - **Category Organization**: Groups metrics by prefix (python*, process*, task*framework*\*)
  - **Summary Dashboard**: Top-level cards (total categories, total metrics, active threads, active workers)
  - **Smart Display Types**:
    - Simple metrics: Large bold values
    - Labeled metrics: Organized tables
    - Histograms: Visual bar charts with bucket visualization
  - **Value Formatting**: K/M suffixes, scientific notation, proper decimals
  - **Auto-refresh**: Toggle for 30-second automatic updates
- **API Endpoints**: `GET /metrics` (Prometheus text format)
- **Parser Logic**:
  - Extracts HELP comments (metric descriptions)
  - Extracts TYPE comments (counter, gauge, histogram, summary)
  - Parses metric values with labels (e.g., `{generation="0"}`)
  - Groups histogram buckets for visualization

### metadata.html

- **Purpose**: Display task metadata and artifact schemas
- **Unique Features**:
  - **Overview Section**: Task name, version, description, framework/API versions, last updated timestamp
  - **Capability Cards**: Visual indicators for Database, File Storage, Scheduler, Webhooks (enabled/disabled)
  - **Input Schemas**: Display artifact schemas with fields table and optional JSON schema
  - **Output Schemas**: Display artifact schemas with fields table and optional JSON schema
  - **JSON Syntax Highlighting**: Color-coded JSON display with keys, strings, numbers, booleans
  - **Copy to Clipboard**: Easy copying of schema JSON for integration/documentation
  - **Field Tables**: Organized display of field name, type, required status, and description
- **API Endpoints**: `GET /task/metadata` (No authentication required)
- **Error Handling**: Special handling for 503 (task not registered) vs other errors
- **Display Features**:
  - Empty state when no schemas defined
  - Capability cards with visual indicators (checkmark/X icon)
  - Formatted JSON with syntax highlighting in dark theme
  - Responsive grid layout for capability cards

### threads.html

- **Purpose**: List all threads with filtering
- **Unique Features**:
  - State filter dropdown
  - Pagination (offset-based)
  - Thread actions (view, stop)
- **API Endpoints**: `/threads`, `/threads/{id}:stop`

### thread-create.html

- **Purpose**: Create new threads with full API compliance
- **Unique Features**:
  - **Dynamic Input Artifacts**:
    - Add/remove multiple artifacts
    - Support for 4 artifact kinds: `text`, `json`, `url`, `rich_text`
    - Per-artifact configuration: kind, ref, media_type, explain
    - Content fields dynamically adapt based on kind selection
    - Client-side validation (at least one artifact required)
  - **Task Parameters**: JSON editor for task-specific configuration (e.g., model settings, thresholds)
  - **Metadata Editor**: JSON editor for custom metadata with auto-population from settings
  - **Execution Mode Toggle**: Sync (wait) vs Async (background)
  - **Advanced Options** (collapsible):
    - **Timeout Configuration**: Execution timeout in seconds (minimum: 1)
    - **Idempotency Key**: Prevent duplicate thread creation
    - **Multiple Webhooks**: Add/remove webhook callbacks with custom events and optional API key authentication
  - **API Headers Section**: Displays and allows editing X-API-Key, X-User-ID, X-App-ID
  - **Client-Side Validation**:
    - Required field validation
    - JSON syntax validation for params, metadata, and JSON artifacts
    - Timeout numeric validation
    - URL format validation for webhooks
    - Artifact-specific field validation
  - **Error Handling**: Detailed error messages with artifact numbering
  - **Loading States**: Visual feedback during submission
- **API Endpoints**: `POST /threads`
- **JavaScript Functions**:
  - `addInputArtifact()` - Add new artifact dynamically
  - `removeInputArtifact(button)` - Remove artifact (prevents removing last one)
  - `updateArtifactFields(selectElement)` - Dynamic field rendering based on kind
  - `addWebhook()` - Add webhook configuration
  - `removeWebhook(button)` - Remove webhook
  - `collectInputArtifacts()` - Parse and validate all artifacts
  - `collectWebhooks()` - Parse all webhook configurations (including callback URL, events, and optional API key)
  - `createThread(event)` - Main form submission handler
- **ThreadCreateRequest Fields** (all supported):
  - `mode` ✅ (sync/async)
  - `inputs` ✅ (multiple artifacts with text/json/url/rich_text)
  - `params` ✅ (task-specific parameters)
  - `metadata` ✅ (custom metadata + auto-populated user_id/app_id)
  - `webhooks` ✅ (multiple webhooks with events and optional API key for authentication)
  - `idempotency_key` ✅ (duplicate prevention)
  - `timeout_seconds` ✅ (execution timeout)

### thread-detail.html

- **Purpose**: View thread details
- **Unique Features**:
  - Thread overview cards
  - Error display
  - Actions (stop, retry)
  - Input/output artifacts preview
- **API Endpoints**: `/threads/{id}`, `/threads/{id}:stop`, `/threads/{id}:retry`

### thread-artifacts.html

- **Purpose**: Advanced artifact management for a specific thread
- **Unique Features**:
  - Multi-filter (kind, direction, ref pattern, archived)
  - Artifact detail modal
  - Copy reference to clipboard
  - Pagination (cursor-based)
- **API Endpoints**: `/threads/{id}/artifacts`

### artifacts.html

- **Purpose**: List and manage all artifacts across threads
- **Unique Features**:
  - **Table Layout**: Clean table format similar to threads.html
  - **Comprehensive Filtering**:
    - Ref pattern (with wildcard support)
    - Kind (15 artifact types)
    - Media type
    - Thread ID
    - App ID
    - Include archived toggle
  - **Icon-Based Actions**: View (eye), Download (arrow), Archive (box), Delete (trash)
  - **Artifact Operations**:
    - View details in modal (full metadata and content)
    - Download files and URLs via pre-signed URLs
    - Archive (soft delete)
    - Delete permanently with confirmation
  - **Pagination**: Offset-based pagination (previous/next buttons work)
  - **Table Columns**:
    - Ref/ID (with archived badge)
    - Kind (color-coded badge)
    - Media Type
    - Thread (clickable link)
    - App ID
    - Created timestamp
    - Actions (icon buttons)
  - **Confirmation Modals**: Separate modal for destructive actions (archive, delete)
  - **Debounced Filters**: Text inputs debounced at 500ms to reduce API calls
- **API Endpoints**: 
  - `GET /artifacts` (list with filters)
  - `GET /artifacts/{id}/download` (download URL)
  - `POST /artifacts/{id}:archive` (archive)
  - `DELETE /artifacts/{id}` (delete)
- **JavaScript Functions**:
  - `loadArtifacts()` - Fetch artifacts with filters and pagination
  - `createArtifactRow()` - Generate table row HTML
  - `viewArtifact()` - Open detail modal
  - `quickDownload/Archive/Delete()` - Quick actions from list
  - `loadPreviousPage/NextPage()` - Pagination navigation
  - `resetAndLoadArtifacts()` - Reset pagination on filter change
  - `debounceLoadArtifacts()` - Debounced filter updates

### webhooks.html

- **Purpose**: List and manage webhook subscriptions
- **Unique Features**:
  - **Table Layout**: Clean table format with webhook subscriptions
  - **Filtering**:
    - Status filter (enabled/disabled)
    - Show limit (10/25/50/100)
  - **Navigation**: Links to create/edit pages (following thread pattern)
  - **Icon-Based Actions**: View (eye), Edit (link), Delete (trash)
  - **Webhook Operations**:
    - Navigate to create page
    - Navigate to edit page with webhook ID
    - Delete webhooks with confirmation modal
    - View webhook details (navigates to webhook-details page)
  - **Pagination**: Offset-based pagination with total count
  - **Table Columns**:
    - URL (with webhook ID below)
    - Status (Enabled/Disabled badge)
    - Events (shows count of include/exclude or "All events")
    - Scope (shows scope filters or "Global")
    - Created timestamp
    - Actions (icon buttons)
- **API Endpoints**:
  - `GET /webhooks` (list with filters)
  - `DELETE /webhooks/{id}` (delete)
- **JavaScript Functions**:
  - `loadWebhooks()` - Fetch webhooks with filters and pagination
  - `createWebhookRow()` - Generate table row HTML
  - `deleteWebhook(id)` - Open delete confirmation modal
  - `confirmDelete()` - Execute delete operation
  - `viewWebhook(id)` - Navigate to webhook details page

### webhook-create.html

- **Purpose**: Create new webhooks or edit existing ones (dual-purpose page)
- **Unique Features**:
  - **Form-Based Layout**: Dedicated page for webhook configuration
  - **Auto-Detection**: Detects edit mode from URL path (`/webhooks/edit/{id}`)
  - **Configuration Options**:
    - URL input with validation (must start with http:// or https://)
    - Enable/disable checkbox
    - Timeout input (1-60 seconds) with validation
    - Event filters dropdown (All Events, Include, Exclude)
    - Event types textarea (shown conditionally)
    - Scope inputs (thread_id, user_id, app_id, tenant_id)
  - **Loading State**: Shows spinner while loading existing webhook data
  - **Form Validation**: Client-side validation with HTML5 attributes
  - **Submit Button State**: Disables during submission to prevent double-submit
- **API Endpoints**:
  - `GET /webhooks/{id}` (load webhook for editing)
  - `POST /webhooks` (create new webhook)
  - `PATCH /webhooks/{id}` (update existing webhook)
- **JavaScript Functions**:
  - `loadWebhookForEdit()` - Fetch and populate form with existing webhook data
  - `saveWebhook(event)` - Submit form (create or update based on editingWebhookId)
- **Navigation**: Redirects to `/ui/webhooks` on success or error

### webhook-details.html

- **Purpose**: Display webhook configuration and delivery history
- **Unique Features**:
  - **Webhook Configuration Display**:
    - Complete webhook information (ID, URL, status, timeout, created by, timestamps)
    - Secret management (masked by default, toggle visibility, copy to clipboard)
    - Event filters display (include/exclude lists)
    - Scope display (thread, user, app, tenant)
    - Data filters display (detail level, download URLs, logs, metrics, artifact selectors)
  - **Quick Actions**:
    - Enable/Disable toggle button
    - Regenerate secret (with confirmation)
    - Delete webhook (with confirmation)
  - **Delivery History**: Embedded deliveries-table component loaded via htmx
  - **Back Navigation**: Return to webhooks list
- **API Endpoints**:
  - `GET /webhooks/{id}` (get webhook details)
  - `PATCH /webhooks/{id}` (toggle enabled status)
  - `POST /webhooks/{id}:regenerate-secret` (regenerate secret)
  - `DELETE /webhooks/{id}` (delete webhook)
- **JavaScript Functions**:
  - `loadWebhook()` - Fetch webhook details
  - `displayWebhook(webhook)` - Render webhook configuration
  - `toggleWebhook()` - Enable/disable webhook
  - `regenerateSecret()` - Regenerate webhook secret
  - `toggleSecretVisibility()` - Show/hide secret
  - `copySecret()` - Copy secret to clipboard
  - `deleteWebhookFromDetails()` - Open delete confirmation
  - `confirmDelete()` - Execute delete and redirect

### deliveries-table.html (Component)

- **Purpose**: Reusable component for displaying webhook delivery history
- **Unique Features**:
  - **Filtering**:
    - Status filter (success/failed)
    - Thread ID filter (with debouncing)
    - Show limit (10/25/50/100)
  - **Table Layout**: Delivery records with status, event type, thread, response info
  - **Pagination**: Offset-based pagination with total count
  - **Delivery Details Modal**: Shows complete delivery information:
    - Delivery ID, status, event type, timestamp
    - Status code and response time
    - Delivery URL
    - Thread and Run IDs (with links)
    - Error message (if failed)
    - Full event payload (JSON formatted)
  - **Table Columns**:
    - Status (color-coded badge: green=success, red=failed)
    - Event Type
    - Thread ID (clickable link to thread details)
    - Status Code
    - Response Time (in milliseconds)
    - Timestamp
    - Actions (View icon button)
- **API Endpoints**:
  - `GET /webhooks/{webhook_id}/deliveries` (list deliveries with filters)
  - `GET /webhooks/{webhook_id}/deliveries/{delivery_id}` (get delivery details)
- **JavaScript Functions**:
  - `initDeliveriesTable(webhookId)` - Initialize component with webhook ID
  - `loadDeliveries()` - Fetch deliveries with filters and pagination
  - `displayDeliveries(data)` - Render delivery table
  - `createDeliveryRow(delivery)` - Generate table row HTML
  - `viewDeliveryDetails(deliveryId)` - Fetch and display delivery details in modal
  - `displayDeliveryDetails(delivery)` - Render delivery details modal content
  - `loadDeliveriesPreviousPage/NextPage()` - Pagination navigation
  - `resetAndLoadDeliveries()` - Reset pagination on filter change
  - `debounceLoadDeliveries()` - Debounced filter updates
- **Integration**: Loaded via htmx in webhook-details.html and initialized with `initDeliveriesTable(webhookId)`

### schedules.html

- **Purpose**: List and manage cron-based task schedules
- **Unique Features**:
  - **Table Layout**: Clean table format with schedule information
  - **Filtering**:
    - State filter (active, paused, canceled)
    - Show limit (10/25/50/100)
  - **Navigation**: Links to create/edit pages (following webhook pattern)
  - **Icon-Based Actions**: View (eye), Edit (pencil), Cancel (X)
  - **Schedule Operations**:
    - Navigate to create page
    - Navigate to edit page with schedule ID
    - Cancel schedules with confirmation modal
    - View schedule details (navigates to schedule-details page)
  - **Pagination**: Offset-based pagination with total count
  - **Table Columns**:
    - Cron expression (with schedule ID below)
    - State (Active/Paused/Canceled badge)
    - Timezone
    - Concurrency policy
    - Created timestamp
    - Actions (icon buttons)
- **API Endpoints**:
  - `GET /schedules` (list with filters)
  - `POST /schedules/{schedule_id}:cancel` (cancel schedule)
- **JavaScript Functions**:
  - `loadSchedules()` - Fetch schedules with filters and pagination
  - `createScheduleRow(schedule)` - Generate table row HTML
  - `cancelSchedule(id)` - Open cancel confirmation modal
  - `confirmCancel()` - Execute cancel operation
  - `resetAndLoadSchedules()` - Reset pagination on filter change
  - `loadPreviousPage/NextPage()` - Pagination navigation

### schedule-create.html

- **Purpose**: Create new schedules or edit existing ones (dual-purpose page)
- **Unique Features**:
  - **Form-Based Layout**: Dedicated page for schedule configuration
  - **Auto-Detection**: Detects edit mode from URL path (`/schedules/edit/{id}`)
  - **Configuration Options**:
    - Cron expression input with format help
    - Timezone input (IANA timezone identifier)
    - Initial state selection (active/paused)
    - Input artifacts template with dynamic add/remove
    - Task parameters (JSON editor)
    - Custom metadata (JSON editor)
    - Concurrency policy (allow, forbid, replace)
    - Max retry attempts (minimum: 1)
  - **Loading State**: Shows spinner while loading existing schedule data
  - **Form Validation**: Client-side validation with HTML5 attributes and JSON validation
  - **Submit Button State**: Disables during submission to prevent double-submit
- **API Endpoints**:
  - `GET /schedules/{id}` (load schedule for editing)
  - `POST /schedules` (create new schedule)
  - `PATCH /schedules/{id}` (update existing schedule)
- **JavaScript Functions**:
  - `loadScheduleForEdit()` - Fetch and populate form with existing schedule data
  - `populateForm(schedule)` - Fill form fields with schedule data
  - `addInput(existingInput)` - Add input artifact to template
  - `removeInput(button)` - Remove input artifact
  - `updateInputFields(selectElement, existingInput)` - Update content fields based on artifact kind
  - `collectInputs()` - Parse and validate all input artifacts
  - `saveSchedule(event)` - Submit form (create or update based on editingScheduleId)
- **Navigation**: Redirects to `/ui/schedules/{id}` on success

### schedule-details.html

- **Purpose**: Display schedule configuration and run history
- **Unique Features**:
  - **Schedule Configuration Display**:
    - Complete schedule information (ID, cron, timezone, state, concurrency, timestamps)
    - Input artifacts template display
    - Task parameters display (JSON formatted)
    - Metadata display (JSON formatted)
  - **Quick Actions**:
    - Pause/Activate toggle button (disabled for canceled schedules)
    - Edit schedule button (links to edit page)
    - Cancel schedule button (with confirmation)
  - **Run History**: Embedded runs-table component loaded via htmx
  - **Breadcrumb Navigation**: Return to schedules list
- **API Endpoints**:
  - `GET /schedules/{id}` (get schedule details)
  - `PATCH /schedules/{id}` (toggle state: active/paused)
  - `POST /schedules/{id}:cancel` (cancel schedule)
- **JavaScript Functions**:
  - `loadSchedule()` - Fetch schedule details
  - `displaySchedule(schedule)` - Render schedule configuration
  - `toggleSchedule()` - Pause/activate schedule
  - `cancelScheduleFromDetails()` - Open cancel confirmation
  - `confirmCancel()` - Execute cancel and redirect
- **Breadcrumb**: Shows "Schedules > {schedule_id}"

### runs-table.html (Component)

- **Purpose**: Reusable component for displaying schedule run history
- **Unique Features**:
  - **Filtering**:
    - State filter (pending, running, succeeded, failed, stopped, timeout, skipped)
    - Show limit (10/25/50/100)
  - **Table Layout**: Run records with state, scheduled time, attempts, and threads
  - **Pagination**: Offset-based pagination with total count
  - **Run Details Modal**: Shows complete run information:
    - Run ID, state, scheduled times (local and UTC)
    - Attempt number vs max attempts
    - Created, started, and finished timestamps
    - Thread IDs (clickable links to thread details)
    - Labels and metrics (JSON formatted)
  - **Table Columns**:
    - Run ID (font-mono)
    - State (color-coded badge: yellow=pending, blue=running, green=succeeded, red=failed, etc.)
    - Scheduled For (Local timezone)
    - Attempt (current/max format)
    - Threads (clickable links to thread details)
    - Actions (View icon button)
- **API Endpoints**:
  - `GET /schedules/{schedule_id}/runs` (list runs with filters)
  - `GET /schedules/{schedule_id}/runs/{run_id}` (get run details)
- **JavaScript Functions**:
  - `initRunsTable(scheduleId)` - Initialize component with schedule ID
  - `loadRuns()` - Fetch runs with filters and pagination
  - `displayRuns(data)` - Render run table
  - `createRunRow(run)` - Generate table row HTML
  - `viewRunDetails(runId)` - Fetch and display run details in modal
  - `displayRunDetails(run)` - Render run details modal content
  - `loadRunsPreviousPage/NextPage()` - Pagination navigation
  - `resetAndLoadRuns()` - Reset pagination on filter change
  - `closeRunDetailsModal()` - Close run details modal
- **Integration**: Loaded via htmx in schedule-details.html and initialized with `initRunsTable(scheduleId)`

### files.html

- **Purpose**: List recently uploaded files (session-based)
- **Unique Features**:
  - **Recently Uploaded Files**: Session-based file list showing uploaded files from this session
  - **File Operations**:
    - Copy file reference to clipboard
    - Download files via pre-signed URLs
    - View file metadata (size, media type, SHA256 hash, created timestamp)
  - **Visual Feedback**: Status badges (Uploaded/Pending Upload)
  - **File Information Display**: File name, size, media type, timestamps, SHA256 hash
  - **Navigation**: Link to upload page (`/ui/files/upload`)
- **API Endpoints**:
  - `GET /files/{file_ref}` (download file)
- **JavaScript Functions**:
  - `loadUploadedFiles()` - Load files from sessionStorage
  - `renderFilesList(files)` - Render uploaded files table
  - `copyFileRef(fileRef)` - Copy file reference to clipboard
  - `downloadFile(fileRef)` - Open download URL in new tab
  - `showSuccess(message)` - Display success notification toast
  - `formatSize(bytes)` - Format file size display
  - `formatDateTime(dateString)` - Format timestamp display
  - `escapeHtml(text)` - HTML escaping for security
- **Session Storage**: Files loaded from `sessionStorage.getItem("uploaded_files")`
- **Info Banner**: Explains that UI shows session-based uploads; for complete file list, use API or filter artifacts
- **Empty State**: Helpful message when no files uploaded yet

### file-upload.html

- **Purpose**: Dedicated page for uploading files
- **Unique Features**:
  - **Two Upload Methods**:
    - **Direct Upload**: Single-request file upload with multipart/form-data
    - **Pre-signed URL**: Two-step upload process (generate URL, then PUT file)
  - **Drag and Drop**: Interactive drop zone for file selection (direct upload only)
  - **Upload Progress**: Real-time progress bar with percentage display (direct upload)
  - **Upload Method Toggle**: Switch between direct and pre-signed upload methods
  - **File Selection**: Click to browse or drag and drop
  - **Visual Feedback**: File info preview, progress bar, success notifications
  - **Breadcrumb Navigation**: Files > Upload
- **API Endpoints**:
  - `POST /files` (direct file upload with multipart/form-data)
  - `POST /uploads` (generate pre-signed upload URL)
- **JavaScript Functions**:
  - `setupDragAndDrop()` - Initialize drag and drop functionality for drop zone
  - `setupPresignedFormListeners()` - Setup input listeners for presigned form validation
  - `selectUploadMethod(method)` - Switch between direct/presigned upload UI
  - `handleFileSelect(event)` - Process selected file and display info
  - `clearFileSelection()` - Reset file selection and hide info
  - `updatePresignedButton()` - Update generate button state based on form validity
  - `uploadFileDirect()` - Direct upload with XMLHttpRequest for progress tracking
  - `generatePresignedUrl()` - Create pre-signed upload URL
  - `saveToSessionStorage(fileData)` - Save file to sessionStorage
  - `showSuccess(message)` - Display success notification toast
  - `formatSize(bytes)` - Format file size display
- **Upload Flow (Direct)**:
  1. User selects file (click or drag-drop)
  2. File info displayed with preview
  3. User clicks "Upload File"
  4. XMLHttpRequest with progress tracking
  5. File saved to sessionStorage on success
  6. Redirects to `/ui/files`
- **Upload Flow (Pre-signed)**:
  1. User enters filename, media type, size
  2. User clicks "Generate URL"
  3. POST to `/uploads` to get pre-signed URL
  4. URL displayed in form for external use
  5. File_ref saved to sessionStorage as "Pending Upload"
  6. User stays on page to copy URL
- **Session Storage**: Files saved to `sessionStorage.setItem("uploaded_files", JSON.stringify(files))`
- **Form Validation**: Required fields validated, buttons disabled when invalid

---

## 🚀 Migration Guide (to Node.js)

This UI is designed to be easily portable to Node.js:

### 1. Component System

**Current**: htmx loads components
**Future**: Express with EJS/Pug/Handlebars templates

```javascript
// Express route
app.get("/ui/threads", (req, res) => {
  res.render("threads", {
    sidebar: renderComponent("sidebar"),
  });
});
```

### 2. State Management

**Current**: localStorage
**Future**: Express sessions or JWT tokens

```javascript
// Session middleware
app.use(
  session({
    secret: "secret-key",
    resave: false,
    saveUninitialized: true,
  })
);
```

### 3. API Communication

**Current**: Fetch with headers from localStorage
**Future**: Server-side API calls with session data

```javascript
// Server-side API call
const response = await fetch("http://api/threads", {
  headers: {
    "X-API-Key": req.session.apiKey,
  },
});
```

### 4. Routes

**Current**: FastAPI FileResponse
**Future**: Express routes

```javascript
app.get("/ui/:page", (req, res) => {
  res.sendFile(`pages/${req.params.page}.html`);
});
```

---

## 📚 Reference

### API Endpoints (from openapi-enhanced.yaml)

- `GET /health` - Health check (no auth)
- `GET /metrics` - Prometheus metrics (text format, no auth)
- `GET /task/metadata` - Task metadata (no auth)
- `GET /threads` - List threads
- `POST /threads` - Create thread
- `GET /threads/{id}` - Get thread details
- `POST /threads/{id}:stop` - Stop thread
- `POST /threads/{id}:retry` - Retry thread
- `GET /threads/{id}/artifacts` - List artifacts

### External Resources

- **htmx**: https://htmx.org/docs/
- **Tailwind CSS**: https://tailwindcss.com/docs
- **FastAPI**: https://fastapi.tiangolo.com/
- **OpenAPI**: `specs/initial/openapi-enhanced.yaml`

---

## ✅ AI Agent Checklist

When working on this codebase:

1. **Before Adding Features**:

   - [ ] Read this file completely
   - [ ] Check `openapi-enhanced.yaml` for API endpoints
   - [ ] Review existing similar pages for patterns
   - [ ] Understand the component system (sidebar)

2. **During Development**:

   - [ ] Follow existing naming conventions
   - [ ] Use localStorage for credentials
   - [ ] Include auth headers in API calls
   - [ ] Handle loading/error/empty states
   - [ ] Use Tailwind CSS utilities
   - [ ] Test in browser DevTools

3. **After Implementation** (⚠️ CRITICAL):
   - [ ] **UPDATE ARCHITECTURE.md** with:
     - New route in "Current Routes" table
     - New page in "Directory Structure"
     - New page in "Page-Specific Details" section
     - New patterns or conventions used
   - [ ] **UPDATE README.md** with:
     - New feature in "Overview" section
     - New feature in "Features" section
     - New file in "Project Structure"
   - [ ] Check for console errors
   - [ ] Verify sidebar loads correctly
   - [ ] Test all states (loading, error, success, empty)
   - [ ] Verify health status appears and updates

**DOCUMENTATION IS NOT OPTIONAL**: Future developers and AI agents depend on these files being accurate and up-to-date. Treat documentation updates with the same importance as code changes.

---

**Last Updated**: 2025-11-06  
**Maintainer**: Task Framework Team
