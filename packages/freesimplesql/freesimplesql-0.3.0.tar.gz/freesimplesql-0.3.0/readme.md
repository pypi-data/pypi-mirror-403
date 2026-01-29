# FreeSimpleSQL

A modern, user-friendly SQL database browser and query tool powered by AI. FreeSimpleSQL simplifies database interactions with a clean interface, AI-assisted query generation, and powerful visualization features.

## ✨ Features

*   **AI SQL Generator**: Describe your query in plain English (e.g., "Show me messages grouped by type") and let the AI generate the SQL for you.
*   **Intuitive Interface**: Clean, dark-themed UI built with FreeSimpleGUI.
*   **Smart Query History**:
    *   Automatically saves your queries and AI prompts.
    *   Access previous queries from a dropdown list.
    *   Persists history across sessions (up to 300 records).
*   **Dynamic Data Table**:
    *   Automatically adjusts columns based on your query results.
    *   Handles complex queries, aggregations, and joins.
    *   Pagination support for large datasets.
    *   **Export to CSV**: One-click copy of table data to clipboard.
*   **Detailed Record View**:
    *   Select any row to view full details.
    *   **JSON View**: Pretty-printed JSON view for complex data fields.
    *   **Plain Text View**: Clean key-value pair display.
*   **Keyboard Shortcuts**: speed up your workflow with intuitive hotkeys.
    *   `Alt-P`: Focus AI Prompt
    *   `Alt-G`: Generate & Apply SQL
    *   `Alt-S`: Execute Query
    *   `Alt-Q`: Focus Query Editor
*   **Database Management**:
    *   Import/Export SQLite databases via the File menu.
    *   Theme selection support.

## 🚀 Getting Started

### Prerequisites

*   Python 3.8+
*   `uv` package manager (recommended) or `pip`

### Installation

1.  Clone the repository:
    ```bash
    git clone <repository_url>
    cd freesimplesql
    ```

2.  Install dependencies:
    ```bash
    uv sync
    # or
    pip install -r requirements.txt
    ```

3.  Run the application:
    ```bash
    uv run -m freesimplesql
    # or
    python -m freesimplesql
    ```

## 📖 Usage Guide

### 1. AI SQL Generation
1.  Press **`Alt-P`** to focus the AI Prompt box.
2.  Type your request (e.g., *"Count total messages per source IP"*).
3.  Press **`Alt-G`**. The system will generate the SQL and automatically place it in the query editor.
4.  Press **`Alt-S`** to execute.

### 2. Manual Querying
1.  Press **`Alt-Q`** to focus the SQL editor.
2.  Type your SQL query (e.g., `SELECT * FROM message WHERE sn > 100`).
3.  Click **Search** or press **`Alt-S`**.

### 3. Using History
*   Select a previous query from the **History dropdown** above the query editor.
*   The editor will populate with the query AND the original AI prompt used to create it (if applicable).

### 4. Configuration
*   **AI Settings**: Go to `AI -> LLM Settings` to configure your API key and preferred model.
*   **Themes**: Change the visual style via the `Theme` menu.

## 🛠️ Technology Stack

*   **GUI**: [FreeSimpleGUI](https://github.com/spyoungtech/FreeSimpleGUI)
*   **Database**: SQLite via [SQLModel](https://sqlmodel.tiangolo.com/) & [SQLAlchemy](https://www.sqlalchemy.org/)
*   **Data Handling**: Pandas (internal usage)
*   **AI Integration**: OpenRouter API compatible

## 📝 License

This project is open-source and available under the MIT License.