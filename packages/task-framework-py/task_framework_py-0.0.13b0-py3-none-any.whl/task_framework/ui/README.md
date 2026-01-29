# Task Framework Web UI

A modern, responsive web interface for interacting with the Task Framework API, built with **htmx**, **Tailwind CSS**, and **vanilla JavaScript**.

> **⚠️ IMPORTANT FOR DEVELOPERS & AI AGENTS**  
> When adding new features, pages, or components, **ALWAYS UPDATE BOTH**:
>
> - `README.md` (user-facing documentation)
> - `ARCHITECTURE.md` (technical documentation)
>
> This ensures consistency and helps future developers understand the system.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Architecture](#architecture)
- [Development](#development)
- [Extending the UI](#extending-the-ui)

## 🎯 Overview

This web UI provides a user-friendly interface to manage and monitor Task Framework operations without writing code. It includes:

- **Settings Management**: Configure API credentials (X-API-Key, X-App-ID, X-User-ID)
- **Task Metadata**: View task information, capabilities, and artifact schemas
- **Thread Management**: Create, list, view, stop, and retry threads
- **Artifact Management**: Browse, filter, and view thread artifacts
- **Health Monitoring**: Real-time system health status
- **Metrics Dashboard**: View Prometheus metrics in a human-readable format

## ✨ Features

### 🔐 Settings Page (`/ui/settings`)

- Manage API authentication credentials
- Stored securely in browser's `localStorage`
- Show/hide API key toggle
- Validation and auto-save functionality

### 🧵 Threads Management (`/ui/threads`)

- List all threads with filtering (state, limit, pagination)
- Real-time thread state updates
- Quick actions: View details, Stop running threads
- Beautiful state badges (queued, running, succeeded, failed, etc.)

### ➕ Thread Creation (`/ui/threads/create`)

- Dedicated page for creating new threads
- Execution mode selection (sync/async)
- **Multiple input artifacts** with dynamic add/remove:
  - Text artifacts (plain text or markdown/rich text)
  - JSON artifacts (structured data)
  - URL artifacts (resource references)
  - Each artifact supports: kind, ref, media_type, explain
- **Task parameters** (JSON) for task-specific configuration
- **Custom metadata** (JSON) for filtering and organization
- **Advanced options**:
  - Execution timeout (seconds)
  - Idempotency key for duplicate prevention
  - Multiple webhook callbacks with custom events and optional API key authentication

### 📊 Thread Details (`/ui/threads/{thread_id}`)

- Complete thread overview (ID, state, timestamps, duration)
- Error details for failed threads
- Metadata display
- Input/output artifacts
- Actions: Stop, Retry, Refresh, Manage Artifacts

### 📦 Thread Artifacts (`/ui/threads/{thread_id}/artifacts`)

- Advanced artifact filtering (kind, direction, ref pattern)
- Artifact details modal
- Copy artifact references
- Include/exclude archived artifacts
- Pagination support

### 📦 Artifacts Management (`/ui/artifacts`)

- List all artifacts across threads in a clean table layout
- Advanced filtering options:
  - Ref pattern (with wildcard support)
  - Kind (text, file, json, url, etc.)
  - Media type
  - Thread ID
  - App ID
  - Include archived artifacts toggle
- View artifact details in modal
- Download artifacts (files and URLs)
- Archive artifacts (soft delete)
- Delete artifacts permanently
- Icon-based actions with tooltips
- Offset-based pagination (previous/next)
- Confirmation dialogs for destructive actions

### 🔔 Webhooks Management (`/ui/webhooks`)

- List all webhook subscriptions in a clean table layout
- Filter by enabled/disabled status
- Navigate to dedicated create/edit pages
- Delete webhooks with confirmation
- View webhook details page (`/ui/webhooks/{webhook_id}`) showing:
  - Complete webhook configuration
  - Secret management (view/copy/regenerate)
  - Enable/disable webhook
  - Delivery history table with filtering by status and thread_id
  - Delivery details modal with full payload and response
- Pagination support for both webhooks and deliveries
- Icon-based actions (view, edit, delete)
- Reusable deliveries table component

### ➕ Webhook Creation/Edit (`/ui/webhooks/create`, `/ui/webhooks/edit/{webhook_id}`)

- Dedicated page for creating and editing webhooks
- URL configuration with validation (must be http:// or https://)
- Enable/disable toggle
- Timeout settings (1-60 seconds)
- Event filters (include/exclude specific event types)
- Scope filters (thread_id, user_id, app_id, tenant_id)
- Form validation and error handling
- On success, redirects to webhooks list

### 📅 Schedules Management (`/ui/schedules`)

- List all cron-based schedules in a clean table layout
- Filter by state (active, paused, canceled)
- Navigate to dedicated create/edit pages
- Cancel schedules with confirmation
- View schedule details page (`/ui/schedules/{schedule_id}`) showing:
  - Complete schedule configuration (cron, timezone, state, inputs, params)
  - Pause/activate schedule toggle
  - Run history table with filtering by state
  - Run details modal with threads and metrics
- Pagination support for both schedules and runs
- Icon-based actions (view, edit, cancel)
- Reusable runs table component

### ➕ Schedule Creation/Edit (`/ui/schedules/create`, `/ui/schedules/edit/{schedule_id}`)

- Dedicated page for creating and editing schedules
- Cron expression and timezone configuration (IANA timezone)
- Initial state selection (active/paused)
- Input artifacts template with dynamic add/remove:
  - Text, JSON, URL, Rich Text artifacts
  - Each artifact supports: kind, ref, media_type, explain
- Task parameters (JSON) for task-specific configuration
- Custom metadata (JSON) for filtering and organization
- Advanced options:
  - Concurrency policy (allow, forbid, replace)
  - Max retry attempts per run
- Form validation and error handling
- On success, redirects to schedule details

### 🔐 Vault Management (`/ui/credentials`)

Unified encrypted storage for secrets and configuration values.

- List all vault entries in a secure table layout
- **Eye icon** toggle to reveal/hide sensitive values
- Create new vault entries with:
  - Unique name (identifier)
  - Encrypted value (stored securely)
  - Optional description
- Edit existing entries (update value or description)
- Delete entries with confirmation
- Values encrypted at rest using Fernet encryption

### ⚙️ Task Configuration (`/ui/tasks/{task_id}/{version}/config`)

Configure requirements for deployed tasks.

- View task requirements (from `task.yaml`)
- Each requirement can be configured as:
  - **Direct Value**: Enter value inline
  - **Vault Reference**: Link to a vault entry
- Required fields marked with asterisk (*)
- Status badge shows Ready/Incomplete
- Non-blocking validation warnings when required fields are missing

### 📁 Files Management (`/ui/files`)

- List recently uploaded files (session-based)
- Navigate to dedicated upload page
- File operations:
  - Copy file references to clipboard
  - Download uploaded files
  - View file metadata (size, media type, SHA256 hash)
- Visual file information cards with status badges

### ➕ File Upload (`/ui/files/upload`)

- Dedicated page for uploading files
- Two upload methods:
  - **Direct Upload**: Single-request file upload with drag-and-drop support
  - **Pre-signed URL**: Two-step upload for large files or external integrations
- Drag-and-drop file selection
- Real-time progress bar for direct uploads
- Automatic file type detection
- Support for any file type
- Breadcrumb navigation
- On success, redirects to files list

### 💚 Health Dashboard (`/ui`)

- Real-time system health monitoring
- Database status
- File storage status
- Scheduler status
- Auto-refresh every 30 seconds

### 📊 Metrics Dashboard (`/ui/metrics`)

- Prometheus metrics parser (converts text format to readable UI)
- Organized by category (Python, Process, Task Framework components)
- Summary cards showing key metrics
- Visual histogram displays for duration metrics
- Smart value formatting (K/M suffixes, scientific notation)
- Auto-refresh toggle (30 seconds)

### 📋 Task Metadata (`/ui/metadata`)

- Task name, version, and description
- Framework and API version information
- Capability indicators (Database, File Storage, Scheduler, Webhooks)
- Input artifact schemas with field definitions
- Output artifact schemas with field definitions
- JSON schema visualization for deep validation
- Copy-to-clipboard functionality for schemas

## 🛠️ Technology Stack

### Frontend

- **htmx** (v1.9.10): Dynamic HTML updates via AJAX
- **Tailwind CSS** (v3.x via CDN): Utility-first CSS framework
- **Vanilla JavaScript**: No frameworks, pure JavaScript

### Backend

- **FastAPI**: Python web framework serving the UI
- **File-based Architecture**: HTML files served as static resources

### Storage

- **localStorage**: Browser-based storage for user settings
- **No cookies**: All credentials stored client-side

## 📁 Project Structure

```
ui/
├── pages/                      # HTML pages
│   ├── index.html             # Home/Dashboard page
│   ├── settings.html          # Settings configuration
│   ├── metrics.html           # Metrics dashboard
│   ├── metadata.html          # Task metadata page
│   ├── threads.html           # Threads list
│   ├── thread-create.html     # Create thread form
│   ├── thread-detail.html     # Thread details view
│   ├── thread-artifacts.html  # Thread-specific artifacts
│   ├── artifacts.html         # All artifacts management
│   ├── webhooks.html          # Webhooks list
│   ├── webhook-create.html    # Create/edit webhook form
│   ├── webhook-details.html   # Webhook details and delivery history
│   ├── schedules.html         # Schedules list
│   ├── schedule-create.html   # Create/edit schedule form
│   ├── schedule-details.html  # Schedule details and run history
│   ├── credentials.html       # Vault entries list
│   ├── credential-create.html # Create/edit vault entry form
│   ├── task-config.html       # Task configuration page
│   ├── files.html             # Files list
│   └── file-upload.html       # File upload page
│
├── components/                 # Reusable HTML components
│   ├── sidebar.html           # Navigation sidebar (loaded via htmx)
│   ├── deliveries-table.html  # Webhook deliveries table (loaded via htmx)
│   ├── api-utils.html         # Shared API utilities
│   └── runs-table.html        # Schedule runs table (loaded via htmx)
│
├── __init__.py                # FastAPI routes
├── README.md                  # This file
└── ARCHITECTURE.md            # Detailed architecture documentation

```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Task Framework API running
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation

The UI is automatically available when you run the Task Framework server:

```bash
# Start the Task Framework server
python -m task_framework.server

# Access the UI
# http://localhost:8000/ui
```

### First Time Setup

1. Navigate to `/ui/settings`
2. Enter your API key (required)
3. Optionally configure X-App-ID and X-User-ID
4. Click "Save Settings"
5. Start using the UI!

## 🏗️ Architecture

### Component-Based Design

The UI uses a **hybrid component architecture**:

- **Reusable Components**: Loaded via htmx from `/ui/components/`
- **Page-Specific Logic**: Each page has its own JavaScript
- **Shared Styles**: Tailwind CSS utilities throughout

### Sidebar Component

The sidebar (`components/sidebar.html`) is a **reusable component** that:

- Loads via htmx on every page
- Handles navigation highlighting
- Manages connection status
- Displays real-time health status
- Auto-refreshes health every 30 seconds

```html
<!-- How it's loaded in pages -->
<div hx-get="/ui/components/sidebar.html" hx-trigger="load" hx-swap="outerHTML">
  <aside class="w-64 bg-gray-800 text-white flex items-center justify-center">
    <div class="text-gray-400 text-sm">Loading...</div>
  </aside>
</div>
```

### Data Flow

1. **User Settings** → `localStorage` → Auto-injected as HTTP headers
2. **API Requests** → htmx with auth headers → Task Framework API
3. **Responses** → Rendered dynamically via JavaScript
4. **Health Status** → Polled every 30s → Updated in sidebar

### State Management

- **No global state**: Each page manages its own state
- **localStorage** for persistence
- **URL-based navigation**: No client-side routing

## 💻 Development

### Adding a New Page

1. **Create the HTML file** in `pages/`:

```html
<!DOCTYPE html>
<html lang="en" class="h-full">
  <head>
    <meta charset="UTF-8" />
    <title>New Page - Task Framework</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <style>
      /* Custom styles */
      .nav-item {
        transition: all 0.2s ease-in-out;
      }
      .custom-scrollbar::-webkit-scrollbar {
        width: 6px;
      }
    </style>
  </head>
  <body class="h-full bg-gray-50">
    <div class="flex h-screen overflow-hidden">
      <!-- Load sidebar component -->
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

      <!-- Your page content -->
      <main class="flex-1 overflow-y-auto">
        <!-- ... -->
      </main>
    </div>

    <script>
      const STORAGE_KEYS = {
        API_KEY: "tf_api_key",
        APP_ID: "tf_app_id",
        USER_ID: "tf_user_id",
      };

      // Your page logic
    </script>
  </body>
</html>
```

2. **Add a route** in `__init__.py`:

```python
@router.get("/ui/new-page", response_class=FileResponse)
async def ui_new_page():
    """Serve the new page."""
    file_path = UI_DIR / "pages" / "new-page.html"
    return FileResponse(file_path, media_type="text/html")
```

3. **Update sidebar navigation** (if needed) in `components/sidebar.html`

### Adding a Reusable Component

1. Create component file in `components/`:

```html
<!-- components/my-component.html -->
<div class="my-component">
  <!-- Component HTML -->
</div>

<script>
  // Component-specific JavaScript
  (function () {
    console.log("My component loaded");
  })();
</script>
```

2. Add route in `__init__.py`:

```python
@router.get("/ui/components/my-component.html", response_class=FileResponse)
async def ui_component_my_component():
    """Serve my component."""
    file_path = UI_DIR / "components" / "my-component.html"
    return FileResponse(file_path, media_type="text/html")
```

3. Load in pages using htmx:

```html
<div hx-get="/ui/components/my-component.html" hx-trigger="load"></div>
```

### Styling Guidelines

#### Use Tailwind Utilities

```html
<div
  class="flex items-center justify-between p-4 bg-white rounded-lg shadow-md"
>
  <h3 class="text-lg font-semibold text-gray-800">Title</h3>
  <button class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg">
    Action
  </button>
</div>
```

#### Custom Styles for Reusable Patterns

```html
<style>
  .nav-item {
    transition: all 0.2s ease-in-out;
  }
  .nav-item:hover {
    transform: translateX(4px);
  }
</style>
```

### JavaScript Patterns

#### Fetching Data

```javascript
async function fetchData() {
  const apiKey = localStorage.getItem(STORAGE_KEYS.API_KEY);
  const appId = localStorage.getItem(STORAGE_KEYS.APP_ID);
  const userId = localStorage.getItem(STORAGE_KEYS.USER_ID);

  try {
    const response = await fetch("/api/endpoint", {
      method: "GET",
      headers: {
        "X-API-Key": apiKey,
        ...(appId && { "X-App-ID": appId }),
        ...(userId && { "X-User-ID": userId }),
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error("Error:", error);
    showError(error.message);
  }
}
```

#### Displaying States

```javascript
function showLoading() {
  document.getElementById("loading-state").classList.remove("hidden");
  document.getElementById("content").classList.add("hidden");
}

function showContent() {
  document.getElementById("loading-state").classList.add("hidden");
  document.getElementById("content").classList.remove("hidden");
}
```

## 🔧 Extending the UI

### Adding New Navigation Items

Edit `components/sidebar.html`:

```html
<div class="mb-6">
  <h2 class="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-2">
    New Section
  </h2>
  <a
    href="/ui/new-page"
    data-nav-item="new-page"
    class="nav-item flex items-center px-3 py-2 rounded-lg text-gray-300 hover:bg-gray-700 hover:text-white"
  >
    <svg
      class="w-5 h-5 mr-3"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <!-- Icon SVG -->
    </svg>
    <span>New Page</span>
  </a>
</div>
```

### Customizing Theme Colors

Modify Tailwind classes throughout the HTML:

- **Primary**: `bg-blue-600`, `text-blue-600`, `hover:bg-blue-700`
- **Success**: `bg-green-600`, `text-green-600`
- **Danger**: `bg-red-600`, `text-red-600`
- **Dark**: `bg-gray-800`, `text-gray-800`

### Adding API Integrations

All API endpoints are documented in `openapi-enhanced.yaml`. Use these endpoints with:

1. Authentication headers (X-API-Key, X-App-ID, X-User-ID)
2. Proper error handling
3. Loading states

## 📝 Notes

### Browser Compatibility

- Modern browsers with ES6+ support
- localStorage support required
- Tested on: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+

### Security

- All credentials stored in `localStorage` (not cookies)
- No sensitive data sent to external servers
- htmx automatically sanitizes HTML responses

### Performance

- Sidebar component cached by browser
- Health status updates throttled to 30s intervals
- Pagination for large data sets

### Migration to Node.js

The UI is designed to be easily portable to Node.js:

1. Components → Server-side templates (EJS, Pug, etc.)
2. FastAPI routes → Express.js routes
3. localStorage → Session management
4. htmx → Can remain or replace with React/Vue

## 📚 Additional Resources

- **OpenAPI Spec**: `specs/initial/openapi-enhanced.yaml`
- **Architecture Details**: `ARCHITECTURE.md`
- **Task Framework Docs**: `../../../README.md`
- **htmx Documentation**: https://htmx.org/
- **Tailwind CSS**: https://tailwindcss.com/

## 🤝 Contributing

When adding new features:

1. Follow the existing patterns
2. Keep components reusable
3. **ALWAYS update both README.md and ARCHITECTURE.md** with new pages, components, or routes
4. Test across browsers
5. Verify all states (loading, error, success, empty) work correctly

### Documentation Requirements

**CRITICAL**: Every time you add, modify, or remove:

- A new page → Update both README.md (Features section) and ARCHITECTURE.md (Routes & Page-Specific Details)
- A new component → Update both README.md (Project Structure) and ARCHITECTURE.md (Component Architecture)
- A new route → Update both files with route details
- A new pattern/convention → Update ARCHITECTURE.md with examples

This documentation is essential for AI agents and human developers to understand and maintain the codebase.

## 📄 License

Same license as Task Framework (see project root)
