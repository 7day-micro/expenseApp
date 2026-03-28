# Expense Tracking App - MVP Scope & Alignment

## 1. What Are We Building? (The MVP)
We are building a personal finance tracker. The goal for Version 1 (Minimum Viable Product) is to deliver a simple, stable, and fast experience for individual users to track their daily spending.

### ✅ IN SCOPE (Version 1)
* **Authentication:** User signup, login, and private sessions.
* **Expense Management:** Add, edit, delete, and view expenses (Amount, Date, Category, Note).
* **Categories:** Create custom categories and assign them to expenses.
* **History & Search:** A list view of all transactions with basic filtering (by date and category).
* **Dashboard:** A monthly summary showing total spent and simple charts.
* **Simple Budgets:** Set a monthly spending limit per category or overall.

### ❌ OUT OF SCOPE (Do not build these yet)
* Shared accounts (families/teams).
* Receipt uploads (images/files).
* Recurring expenses (automated entries).
* Multi-currency support.
* CSV export/import.
* AI financial insights.



---

## 2. Shared Glossary (Domain Language)
To avoid confusion between Frontend and Backend, we use these exact terms:
* **User:** The account owner. Expenses are strictly private to the User.
* **Expense:** A single outgoing transaction. Must have a positive numeric amount. Refunds are out of scope for MVP.
* **Category:** A grouping for expenses (e.g., "Food", "Transport"). Users can create their own.
* **Budget:** A soft monthly limit set by the user.

---

## 3. Data Model (Core Entities)
Keep the database normalized but simple. Every table should include `created_at` and `updated_at`.

* **Users:** `id`, `email`, `password_hash`
* **Categories:** `id`, `user_id`, `name`, `color/icon`
* **Expenses:** `id`, `user_id`, `category_id`, `amount`, `transaction_date`, `note`
* **Budgets:** `id`, `user_id`, `category_id` (optional), `amount_limit`, `month_year`

---

## 4. Architecture & Workflow Agreements
* **Architecture:** We are building a **Modular Monolith**. Keep backend features (auth, expenses, reports) in clean, separate modules.
* **Delivery Strategy:** We build in **Vertical Slices**. Do not build the entire API first. Build one feature end-to-end (e.g., "Create Expense": DB + API + Frontend UI) before moving to the next.
* **Validation:** Never trust client input. The Frontend will validate for UX, but the Backend MUST validate for security and data integrity.
* **Setup Scripts:** We will use dedicated scripts for local development setup. Note: keep a separate `seed.py` file for creating skills, categories, and dummy users to make local testing easier.

---

## 5. Next Steps for the Team
1.  Agree on the exact JSON request/response format for the `/expenses` endpoint.
2.  Agree on exact Date formats (e.g., ISO 8601 strings only: `YYYY-MM-DDTHH:mm:ss.sssZ`).
3.  Set up the blank repositories and CI/CD pipelines.
