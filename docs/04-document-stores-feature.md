# Document Stores Feature

## Overview
Document Stores allow users to organize documents into collections (folders/groups) for better management and batch operations. This feature introduces a hierarchical organization where users must create stores before uploading documents.

## User Flow

### Landing Page (Stores List View)
- Displays all document stores in grid/list layout
- Each store card shows:
  - Store name
  - Store description (if provided)
  - Document count
  - Created date
  - [Summary] button → Opens modal with status breakdown
- Actions:
  - [Create Store] button (primary action)
  - Click store card → Navigate to Store View
  - Store card actions: Edit, Delete (with confirmation)

### Store View
When a store is selected, user sees:
- **Header:**
  - [← Back] button to return to Stores List
  - Store name (editable inline or via edit button)
  - Store description
  
- **Actions Bar:**
  - [Upload Document] - Opens file picker
  - [Process All] - Trigger processing for all COMPLETED documents
  - [Retry Failed] - Retry all FAILED/PARTIALLY_INDEXED documents
  - [Delete Store] - Delete store and all documents (with confirmation)

- **Search & Filter:**
  - Search bar (searches within this store only)
  - Status filter dropdown
  - Sort options (date, name, size)

- **Documents List:**
  - Shows all documents in this store
  - Individual document actions (view, process, retry, delete, move)
  - Drag-and-drop to move documents between stores
  - Real-time status updates via WebSocket

## Database Schema

### New Table: `document_stores`
```sql
CREATE TABLE document_stores (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at TIMESTAMP,
    
    CONSTRAINT unique_store_name_per_user UNIQUE(user_id, name, is_deleted)
);

CREATE INDEX ix_document_stores_user_id ON document_stores(user_id);
CREATE INDEX ix_document_stores_is_deleted ON document_stores(is_deleted);
```

### Modified Table: `documents`
```sql
ALTER TABLE documents 
ADD COLUMN store_id INTEGER NOT NULL REFERENCES document_stores(id) ON DELETE CASCADE;

CREATE INDEX ix_documents_store_id ON documents(store_id);
```

**Migration Strategy:**
- Create `document_stores` table
- Add `store_id` column to `documents` as NULLABLE first
- For existing documents without stores, handle in application (can be deleted or require manual assignment)
- Make `store_id` NOT NULL after cleanup

## API Endpoints

### Document Stores

#### `GET /api/v1/stores`
Get all stores for current user
- **Response:** List of stores with document counts
```json
[
  {
    "id": 1,
    "name": "Research Papers",
    "description": "Academic research documents",
    "document_count": 12,
    "created_at": "2025-12-27T10:00:00Z",
    "updated_at": "2025-12-27T14:30:00Z"
  }
]
```

#### `POST /api/v1/stores`
Create a new store
- **Body:** `{ "name": "Store Name", "description": "Optional description" }`
- **Response:** Created store object

#### `GET /api/v1/stores/{id}`
Get store details with document statistics
- **Response:** Store object with status breakdown
```json
{
  "id": 1,
  "name": "Research Papers",
  "description": "Academic research documents",
  "document_count": 12,
  "status_breakdown": {
    "uploaded": 0,
    "processing": 2,
    "completed": 1,
    "indexing": 0,
    "indexed": 8,
    "partially_indexed": 0,
    "indexing_failed": 1,
    "failed": 0
  },
  "total_size": 15728640,
  "created_at": "2025-12-27T10:00:00Z"
}
```

#### `PUT /api/v1/stores/{id}`
Update store name/description
- **Body:** `{ "name": "Updated Name", "description": "Updated description" }`
- **Response:** Updated store object

#### `DELETE /api/v1/stores/{id}`
Delete store and ALL documents permanently
- **Response:** Success message with count of deleted documents
- **Note:** Requires confirmation in UI

#### `GET /api/v1/stores/{id}/documents`
Get all documents in a store
- **Query params:** `status`, `search`, `sort`, `page`, `limit`
- **Response:** Paginated document list

#### `POST /api/v1/stores/{id}/documents/upload`
Upload document to specific store
- **Body:** Multipart form data with file and metadata
- **Response:** Document object

#### `POST /api/v1/stores/{id}/process-all`
Process all COMPLETED documents in store
- **Response:** List of task IDs for queued processing jobs

#### `POST /api/v1/stores/{id}/retry-all-failed`
Retry all FAILED/PARTIALLY_INDEXED/INDEXING_FAILED documents
- **Response:** List of task IDs for queued retry jobs

### Documents

#### `PATCH /api/v1/documents/{id}/move`
Move document to another store
- **Body:** `{ "store_id": 2 }`
- **Response:** Updated document object

## Frontend Components

### New Components

#### `StoresListPage.tsx`
- Grid/list view of all stores
- Create store modal/dialog
- Store cards with actions
- Summary modal showing status breakdown

#### `StoreViewPage.tsx`
- Store header with back navigation
- Action buttons (upload, process all, retry all, delete)
- Documents list (reuse existing DocumentsPage logic)
- Search and filter scoped to current store

#### `CreateStoreModal.tsx`
- Form with name (required) and description (optional)
- Validation (name length, uniqueness)

#### `StoreSummaryModal.tsx`
- Display status breakdown chart/stats
- Document count by status
- Total storage used
- Recent activity

#### `MoveDocumentModal.tsx`
- Dropdown/list to select target store
- Confirmation button

### Modified Components

#### `DocumentsPage.tsx`
- Remove from main navigation (now accessed via store view)
- Make it reusable with `store_id` prop
- Add drag-and-drop handlers for moving documents

### State Management

#### `storeStore.ts` (Zustand)
```typescript
interface Store {
  id: number;
  name: string;
  description?: string;
  document_count: number;
  created_at: string;
  updated_at?: string;
}

interface StoreStore {
  stores: Store[];
  currentStore: Store | null;
  isLoading: boolean;
  error: string | null;
  
  fetchStores: () => Promise<void>;
  createStore: (data: CreateStoreData) => Promise<Store>;
  updateStore: (id: number, data: UpdateStoreData) => Promise<Store>;
  deleteStore: (id: number) => Promise<void>;
  setCurrentStore: (store: Store | null) => void;
}
```

### Services

#### `storeService.ts`
```typescript
export const storeService = {
  getAllStores: () => Promise<Store[]>;
  getStore: (id: number) => Promise<StoreDetail>;
  createStore: (data: CreateStoreData) => Promise<Store>;
  updateStore: (id: number, data: UpdateStoreData) => Promise<Store>;
  deleteStore: (id: number) => Promise<void>;
  getStoreDocuments: (id: number, params: QueryParams) => Promise<PaginatedDocuments>;
  processAllDocuments: (id: number) => Promise<{ task_ids: string[] }>;
  retryAllFailed: (id: number) => Promise<{ task_ids: string[] }>;
};
```

## Business Rules

1. **Store Creation:**
   - Name is required (max 255 chars)
   - Name must be unique per user
   - Description is optional

2. **Document Upload:**
   - Can only upload to existing store
   - No upload without store selection
   - Upload button only visible in Store View

3. **Store Deletion:**
   - Permanently deletes ALL documents in store
   - Requires confirmation dialog
   - Shows count of documents to be deleted
   - Cannot be undone

4. **Document Moving:**
   - Can move document between stores via drag-and-drop or modal
   - Updates document's `store_id`
   - Real-time update via WebSocket

5. **Bulk Operations:**
   - Process All: Only processes documents in COMPLETED status
   - Retry All: Only retries FAILED, PARTIALLY_INDEXED, INDEXING_FAILED
   - Delete Store: Deletes all documents regardless of status
   - All bulk operations show progress/results

6. **Search & Filter:**
   - Search scope limited to current store
   - Status filter applies to current store only
   - No cross-store search

7. **Store View:**
   - Single store selection only
   - No "All Documents" view across stores
   - Must select specific store to see documents

## UI/UX Considerations

### Store Cards
- Card design with hover effects
- Show key metrics: document count, last updated
- Quick actions: Summary, Edit, Delete
- Visual indicators for stores with failed documents

### Store Summary Modal
- Pie/donut chart for status distribution
- Table showing status counts
- Recent activity timeline
- Storage usage

### Confirmation Dialogs
- Delete store: "This will permanently delete [X] documents. Type store name to confirm."
- Process all: "Process [X] documents in this store?"
- Retry all: "Retry [X] failed documents?"

### Drag-and-Drop
- Visual feedback during drag
- Drop zones highlighted
- Smooth animations
- Error handling if drop fails

### Empty States
- No stores: "Create your first document store to organize documents"
- Empty store: "No documents yet. Upload your first document"
- No search results: "No documents found matching your search"

## WebSocket Updates

Extend existing WebSocket to include store-level updates:
- Document status changes within store
- Document moved to/from store
- Document deleted from store
- Store document count updates

## Migration Plan

### Phase 1: Database & Backend
1. Create Alembic migration for `document_stores` table
2. Add `store_id` column to `documents` (nullable initially)
3. Create store models and schemas
4. Implement store API endpoints
5. Update document endpoints to handle `store_id`
6. Add bulk operation endpoints

### Phase 2: Frontend
1. Create store state management
2. Build StoresListPage component
3. Build CreateStoreModal component
4. Build StoreSummaryModal component
5. Modify DocumentsPage for store-scoped view
6. Implement drag-and-drop functionality
7. Update routing and navigation

### Phase 3: Testing & Cleanup
1. Test all CRUD operations
2. Test bulk operations
3. Test WebSocket updates
4. Test drag-and-drop
5. Handle existing documents (delete or migrate)
6. Make `store_id` NOT NULL after cleanup
7. Update documentation

## Security Considerations

- Ensure users can only access their own stores
- Validate store_id belongs to user before operations
- Prevent moving documents to stores owned by other users
- Rate limit store creation and bulk operations
- Validate file uploads within store context

## Future Enhancements (Not in Initial Scope)

- Store templates (predefined stores for common use cases)
- Store sharing/collaboration between users
- Store export (download all documents as zip)
- Store-level settings (custom chunking, embedding models)
- Store tags/categories
- Nested stores (folders within folders)
- Store-level access controls
