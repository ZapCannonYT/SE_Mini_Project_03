# DFIP - Entity Relationship Diagram

Source of truth: `backend/app/models/`. GitHub renders the diagram below.

```mermaid
erDiagram
    USERS ||--o{ AUDIT_LOGS : "performs"
    USERS ||--o{ SALES_RECORDS : "creates"
    USERS ||--o{ INVENTORY : "updates"
    USERS ||--o{ FORECASTS : "requests"
    PRODUCTS ||--o| INVENTORY : "has stock"
    PRODUCTS ||--o{ SALES_RECORDS : "sold as"
    PRODUCTS ||--o{ FORECASTS : "forecast for"
    PRODUCTS ||--o{ RECOMMENDATIONS : "planned for"
    FORECASTS ||--|{ FORECAST_POINTS : "contains"
    FORECASTS ||--o{ RECOMMENDATIONS : "based on"

    USERS {
        int id PK
        string name
        string email UK
        string password_hash
        string role "admin | planner | viewer"
        bool is_active
        datetime created_at
    }
    PRODUCTS {
        int id PK
        string sku UK
        string name
        string category
        string unit
        int safety_stock ">= 0"
        float overstock_factor "> 0, default 1.5"
        bool is_active
        datetime created_at
    }
    INVENTORY {
        int product_id PK, FK
        int quantity ">= 0"
        datetime updated_at
        int updated_by FK
    }
    SALES_RECORDS {
        int id PK
        int product_id FK
        date sale_date "unique with product_id"
        int quantity_sold ">= 0"
        int created_by FK
        datetime created_at
    }
    FORECASTS {
        int id PK
        int product_id FK
        int horizon "> 0"
        string unit "week | month"
        string model_name
        string model_version
        datetime generated_at
        int created_by FK
    }
    FORECAST_POINTS {
        int id PK
        int forecast_id FK
        date period_start
        float predicted_qty ">= 0"
    }
    RECOMMENDATIONS {
        int id PK
        int product_id FK
        int forecast_id FK
        int current_stock
        float forecast_demand
        int safety_stock
        float overstock_factor
        int reorder_qty ">= 0"
        string risk "none | stockout | overstock"
        datetime created_at
    }
    AUDIT_LOGS {
        int id PK
        int actor_id FK
        string action
        string entity
        string entity_id
        string result
        text details
        datetime timestamp
    }
    SETTINGS {
        string key PK
        string value
        datetime updated_at
    }
```

## Notes
- Deleting a product deletes its inventory row, sales, forecasts and recommendations (`ON DELETE CASCADE`).
- Deleting a user keeps their records and sets the user reference to NULL (`ON DELETE SET NULL`).
- Recommendations copy the inputs they were calculated from, so DFIP-F-016 can show them later even if stock changes.
- Enums are stored as strings, so the same schema works on SQLite, MySQL and PostgreSQL.
