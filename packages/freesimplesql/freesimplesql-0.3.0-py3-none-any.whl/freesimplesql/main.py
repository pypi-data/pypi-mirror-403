import FreeSimpleGUI as sg
from sqlalchemy.sql import text

from sqlmodel import Field, Session, SQLModel, create_engine, select
from datetime import datetime, timedelta
import random
import ipaddress
import json
from typing import Optional
from faker import Faker
from loguru import logger
from pydantic import field_validator
import shutil
import requests
import os
import pathlib
import sys

# Configuration file path
CONFIG_FILE = "app_config.json"
HISTORY_FILE = "query_history.json"
MAX_HISTORY = 300

# Available themes
THEMES = [
    'DarkBlue3', 'DarkBlue', 'DarkBlue2', 'DarkBlue1',
    'DarkGreen', 'DarkGreen2', 'DarkGreen1',
    'DarkGrey', 'DarkGrey2', 'DarkGrey1',
    'DarkRed', 'DarkRed2', 'DarkRed1',
    'DarkPurple', 'DarkPurple2', 'DarkPurple1',
    'DarkTeal', 'DarkTeal2', 'DarkTeal1',
    'LightBlue', 'LightBlue2', 'LightBlue1',
    'LightGreen', 'LightGreen2', 'LightGreen1',
    'LightGrey', 'LightGrey2', 'LightGrey1',
    'LightRed', 'LightRed2', 'LightRed1',
    'LightPurple', 'LightPurple2', 'LightPurple1',
    'LightTeal', 'LightTeal2', 'LightTeal1',
    'Black', 'Brown', 'SandyBrown', 'Tan',
    'SystemDefault', 'SystemDefaultForReal'
]

def load_config():
    """Load configuration from file."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            return {}
    return {}

def save_config(config):
    """Save configuration to file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        logger.debug("Configuration saved successfully")
    except Exception as e:
        logger.error(f"Error saving config: {e}")

def load_history():
    """Load query history from file."""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading history: {e}")
            return []
    return []

def save_history(history):
    """Save query history to file (max 300 records)."""
    try:
        # Keep only last 300 records
        history_to_save = history[:MAX_HISTORY]
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history_to_save, f, indent=2, ensure_ascii=False)
        logger.debug(f"History saved successfully ({len(history_to_save)} records)")
    except Exception as e:
        logger.error(f"Error saving history: {e}")

class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sn: int
    timestamp: datetime
    src_ip: str
    dst_ip: str
    msg_name: str
    msg_content: str
    hexvalue: str

    @field_validator("timestamp", mode="before")
    def validate_timestamp(cls, value):
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        return value

class DBBrowser:
    def __init__(self):
        self.engine = create_engine("sqlite:///database.db", echo=False)
        self.page_size = 50 * 10
        self.default_query = "SELECT * FROM message"
        self.current_page = 0
        self.total_rows = 0

    @staticmethod
    def setup_db():
        SQLModel.metadata.create_all(DBBrowser.create_engine())
        with Session(DBrowser.create_engine()) as session:
            if not session.exec(select(Message)).first():
                DBrowser.generate_dummy_data()

    @staticmethod
    def create_engine():
        return create_engine("sqlite:///database.db", echo=False)

    @staticmethod
    def generate_dummy_data():
        fake = Faker()
        msg_names = ["INFO", "WARNING", "ERROR", "DEBUG", "CRITICAL"]
        base_time = datetime.now()
        with Session(DBrowser.create_engine()) as session:
            messages = []
            for i in range(1000):
                json_content = {
                    "id": i + 1,
                    "name": fake.name(),
                    "email": fake.email(),
                    "address": fake.address(),
                    "text": fake.text(max_nb_chars=900)
                }
                json_str = json.dumps(json_content)
                hex_value = json_str.encode("utf-8").hex()
                message = Message(
                    sn=i + 1,
                    timestamp=base_time + timedelta(seconds=i),
                    src_ip=str(ipaddress.IPv4Address(random.randint(0, 2**32-1))),
                    dst_ip=str(ipaddress.IPv4Address(random.randint(0, 2**32-1))),
                    msg_name=random.choice(msg_names),
                    msg_content=json_str,
                    hexvalue=hex_value
                )
                messages.append(message)
            session.add_all(messages)
            session.commit()

    def execute_query(self, query_text=None):
        with Session(self.engine) as session:
            try:
                # Calculate LIMIT and OFFSET for pagination
                limit = self.page_size
                offset = self.current_page * self.page_size
                paginated_query = None
                if query_text and query_text.strip():
                    # Remove any existing LIMIT/OFFSET from user query for safety
                    base_query = query_text.strip().rstrip(';')
                    if 'limit' in base_query.lower():
                        base_query = base_query.rsplit('limit', 1)[0].strip()
                    paginated_query = f"{base_query} LIMIT {limit} OFFSET {offset}"
                    logger.debug(f"Executing paginated SQL query: {paginated_query}")
                    result = session.exec(text(paginated_query))
                    # Get column names and data as dictionaries
                    column_names = list(result.keys())
                    all_results = [dict(zip(column_names, row)) for row in result]
                    # Get total rows for pagination info
                    count_query = f"SELECT COUNT(*) FROM ({base_query}) as subquery"
                    total = session.exec(text(count_query)).first()
                    self.total_rows = total[0] if total else 0
                    return all_results, column_names
                else:
                    logger.debug("Executing default paginated query using SQLModel")
                    result = session.exec(select(Message).offset(offset).limit(limit))
                    all_results = list(result)
                    # Get total rows for pagination info
                    self.total_rows = session.exec(select(Message)).count()
                    # Get actual column names from the first result
                    if all_results:
                        # Get column names from the Message model
                        column_names = self.get_columns()
                        all_results = [{col: getattr(row, col) for col in column_names} for row in all_results]
                    else:
                        column_names = self.get_columns()
                    return all_results, column_names
            except Exception as e:
                logger.debug(f"Query error: {e}")
                self.total_rows = 0
                return [], self.get_columns()

    def update_record(self, record_id: int, new_data: dict):
        with Session(self.engine) as session:
            try:
                record = session.get(Message, record_id)
                if not record:
                    return False, "Record not found"
                
                # Update fields
                for key, value in new_data.items():
                    if hasattr(record, key):
                        setattr(record, key, value)
                
                session.add(record)
                session.commit()
                session.refresh(record)
                return True, "Success"
            except Exception as e:
                logger.error(f"Update failed: {e}")
                return False, str(e)

                return False, str(e)

    def get_schema(self):
        try:
            with Session(self.engine) as session:
                # specific for sqlite
                result = session.exec(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='message'")).first()
                if result:
                    return result[0]
                return "Schema not found."
        except Exception as e:
            return f"Error retrieving schema: {e}"

    def get_columns(self):
        return ["id", "sn", "timestamp", "src_ip", "dst_ip", "msg_name", "msg_content", "hexvalue"]

    def get_row_dict(self, row: Message):
        return {
            "id": row.id,
            "sn": row.sn,
            "timestamp": row.timestamp,
            "src_ip": row.src_ip,
            "dst_ip": row.dst_ip,
            "msg_name": row.msg_name,
            "msg_content": row.msg_content,
            "hexvalue": row.hexvalue
        }


def generate_sql_with_ai(prompt: str, model: str, api_key: str, schema: str) -> str:
    """Generate SQL query using OpenRouter API."""
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Clean the API key - remove any whitespace or newlines
        api_key = api_key.strip()
        
        system_prompt = f"""You are a SQL expert. Generate SQL queries based on the user's request.
        
Database Schema:
{schema}

Rules:
- Generate only the SQL query, no explanations
- Use proper SQL syntax for SQLite
- Return only the SELECT statement
- Do not include any markdown formatting or code blocks
- Do not include any text before or after the SQL query"""

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://freesimplesql.app",
            "X-Title": "FreeSimpleSQL"
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 500
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        sql_query = result['choices'][0]['message']['content'].strip()
        
        # Clean up any markdown code blocks if present
        if sql_query.startswith('```'):
            sql_query = sql_query.split('\n', 1)[1]
        if sql_query.endswith('```'):
            sql_query = sql_query.rsplit('\n', 1)[0]
        sql_query = sql_query.strip()
        
        # Remove common prefixes
        for prefix in ['sql', 'SQL', 'sqlite', 'SQLite']:
            if sql_query.lower().startswith(prefix.lower()):
                sql_query = sql_query[len(prefix):].strip()
        
        return sql_query
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {e}")
        return f"Error: API request failed - {str(e)}"
    except Exception as e:
        logger.error(f"Error generating SQL: {e}")
        return f"Error: {str(e)}"


def main():
    # Load configuration
    config = load_config()
    
    # Set theme from config or use default
    theme = config.get('theme', 'DarkBlue3')
    if theme in THEMES:
        sg.theme(theme)
    else:
        sg.theme('DarkBlue3')
    
    browser = DBBrowser()
    columns = browser.get_columns()

    current_page_rows = []  # Store the current page's row objects
    current_columns = columns  # Store current table columns
    query_history_data = load_history()  # Load history from file
    
    # Extract query strings for dropdown
    query_history_list = [item['query'] for item in query_history_data] if query_history_data else []

    def update_table(query_text=None):
        nonlocal current_page_rows, current_columns
        logger.debug("Updating table with new query results")
        rows, new_columns = browser.execute_query(query_text)
        
        # Create table data with proper columns
        table_data = []
        for row in rows:
            if isinstance(row, dict):
                table_data.append([str(row.get(col, '')) for col in new_columns])
            else:
                table_data.append([str(getattr(row, col, '')) for col in new_columns])
        
        # Update table values
        table_elem = window['-TABLE-']
        table_elem.update(values=table_data)
        
        # Show column information prominently
        if new_columns != list(table_elem.ColumnHeadings):
            # Columns changed - show warning and display actual columns
            window['-TABLE-INFO-'].update(
                f"⚠ Query columns: {', '.join(new_columns)} | Showing {len(rows)} rows",
                text_color='orange'
            )
        else:
            window['-TABLE-INFO-'].update(
                f"Showing {len(rows)} rows with columns: {', '.join(new_columns)}",
                text_color='gray'
            )
        
        current_page_rows = rows
        current_columns = new_columns
        max_pages = (browser.total_rows - 1) // browser.page_size + 1 if browser.total_rows > 0 else 1
        window['-PAGE_INFO-'].update(f"Page {browser.current_page + 1} of {max_pages} | Total: {browser.total_rows}")
        
        logger.debug(f"Table updated. Current page: {browser.current_page + 1}, Total pages: {max_pages}, Columns: {new_columns}")

    def copy_table_to_csv():
        """Copy table data to clipboard in CSV format."""
        nonlocal current_page_rows, current_columns
        if not current_page_rows or not current_columns:
            sg.popup_error('No data to copy!')
            return
        
        try:
            csv_lines = []
            csv_lines.append(','.join(current_columns))
            for row in current_page_rows:
                row_values = []
                for col in current_columns:
                    val = str(row.get(col, '') if isinstance(row, dict) else getattr(row, col, ''))
                    if ',' in val or '"' in val or '\n' in val:
                        val = '"' + val.replace('"', '""') + '"'
                    row_values.append(val)
                csv_lines.append(','.join(row_values))
            csv_text = '\n'.join(csv_lines)
            sg.clipboard_set(csv_text)
            sg.popup_quick_message('Table copied to clipboard as CSV!', background_color='green', text_color='white')
        except Exception as e:
            logger.error(f"Error copying table to CSV: {e}")
            sg.popup_error(f'Error copying table: {e}')

    def open_ai_settings():
        """Open AI API settings dialog."""
        ai_layout = [
            [sg.Text("AI API Settings", font=('Any', 14, 'bold'))],
            [sg.HorizontalSeparator()],
            [sg.Text("Model:", size=(10, 1)), 
             sg.Combo([
                 'z-ai/glm-4.7-flash',
                 'openai/gpt-oss-120b',
                 'x-ai/grok-4.1-fast',
                 'google/gemini-2.5-flash-lite'
             ], default_value=config.get('model', 'z-ai/glm-4.7-flash'), key='-AI-MODEL-DLG-', size=(40, 1))],
            [sg.Text("Or enter model manually:", size=(18, 1)), sg.InputText(key='-AI-MODEL-MANUAL-DLG-', size=(30, 1), expand_x=True)],
            [sg.Text("API Key:", size=(10, 1)), sg.InputText(default_text=config.get('api_key', ''), key='-AI-API-KEY-DLG-', password_char='*', size=(40, 1), expand_x=True)],
            [sg.HorizontalSeparator()],
            [sg.Button('Save', key='-SAVE-AI-SETTINGS-', button_color=('white', 'green')), sg.Button('Cancel', key='-CANCEL-AI-DLG-')]
        ]
        
        ai_window = sg.Window('AI API Settings', ai_layout, modal=True, finalize=True, resizable=True, size=(500, 200))
        
        while True:
            event, values = ai_window.read()
            if event in (sg.WIN_CLOSED, '-CANCEL-AI-DLG-'):
                break
            elif event == '-SAVE-AI-SETTINGS-':
                model = values['-AI-MODEL-DLG-']
                manual_model = values['-AI-MODEL-MANUAL-DLG-'].strip()
                api_key = values['-AI-API-KEY-DLG-']
                
                if not api_key:
                    sg.popup_error('Please enter your API key.')
                    continue
                
                final_model = manual_model if manual_model else model
                
                # Save API key to config
                config['api_key'] = api_key
                config['model'] = final_model
                save_config(config)
                
                sg.popup_quick_message('API settings saved!', background_color='green', text_color='white')
                break
        
        ai_window.close()





    
    # AI Builder section (streamlined - auto-applies to query)
    ai_builder_layout = [
        [sg.Text("AI SQL Generator", font=('Any', 14, 'bold'))],
        [sg.Text("Describe what you want to query (alt-p):", size=(30, 1))],
        [sg.Multiline(size=(40, 5), key='-AI-PROMPT-', expand_x=True, tooltip="Enter natural language description of your query (alt-p to focus)")],
        [sg.Button('Generate SQL', key='-GENERATE-SQL-', button_color=('white', 'green'), expand_x=True, tooltip="Generate and apply SQL to query editor (alt-g)")]
    ]
    
    # Controls section (above SQL query)
    controls_section = [
        [sg.Button('Search', key='-SEARCH-', button_color=('white', 'green'), tooltip="Execute query (alt-s)"),
         sg.Button('Reset', key='-RESET-', tooltip="Reset to default query")]
    ]
    
    # Left section (Query builder with AI and controls moved above)
    left_section = [
        [sg.Frame('AI SQL Builder', ai_builder_layout, expand_x=True)],
        [sg.HorizontalSeparator()],
        [sg.Text("SQL Query (alt-q):")],
        [sg.Combo(query_history_list, key='-QUERY-HISTORY-', size=(80, 1), enable_events=True, readonly=True, tooltip="Select from previous queries", expand_x=True)],
        *controls_section,  # Unpack the list
        [sg.Multiline(default_text=browser.default_query, size=(60, 10), key='-QUERY-', expand_x=True, expand_y=True, tooltip="Enter your SQL query here (alt-q to focus)")]
    ]

    # Menu Definition
    menu_def = [
        ['File', ['Export DB', 'Import DB', '---', 'Exit']], 
        ['AI', ['LLM Settings...']],
        ['Theme', THEMES]
    ]

    # Right section - table and detail view with horizontal splitter
    table_area = [
        [sg.Text("", key='-TABLE-INFO-', font=('Any', 10, 'bold'), text_color='orange')],
        [sg.Table(
            values=[],
            headings=columns,
            auto_size_columns=True,
            display_row_numbers=False,
            justification='left',
            num_rows=20,
            key='-TABLE-',
            enable_events=True,
            expand_x=True,
            expand_y=True
        )],
        [
            sg.Button('First', key='-FIRST-'),
            sg.Button('Previous', key='-PREVIOUS-'),
            sg.Text('', key='-PAGE_INFO-', size=(30, 1), justification='center'),
            sg.Button('Next', key='-NEXT-'),
            sg.Button('Last', key='-LAST-'),
            sg.Push(),
            sg.Button('Copy as CSV', key='-COPY-CSV-', button_color=('white', 'purple'))
        ]
    ]
    
    detail_area = [
        [sg.TabGroup([
            [
                sg.Tab('JSON', [[
                    sg.Multiline(size=(40, 10), key='-DETAIL-JSON-', disabled=True, expand_x=True, expand_y=True, font=('Courier', 10))
                ]], key='-JSON-TAB-'),
                sg.Tab('Plain Text', [[
                    sg.Multiline(size=(40, 10), key='-DETAIL-PLAIN-', disabled=True, expand_x=True, expand_y=True, font=('Courier', 10))
                ]], key='-PLAIN-TAB-')
            ]
        ], key='-DETAIL-TABS-', expand_x=True, expand_y=True)]
    ]
    
    # Right section with horizontal pane between table and detail
    right_section = [
        [sg.Pane(
            [
                sg.Column(table_area, expand_x=True, expand_y=True),
                sg.Column(detail_area, expand_x=True, expand_y=True)
            ],
            orientation='vertical',
            relief=sg.RELIEF_GROOVE,
            expand_x=True,
            expand_y=True,
            show_handle=True,
            key='-TABLE-DETAIL-PANE-'
        )]
    ]
    
    layout = [
        [sg.Menu(menu_def)],
        [sg.Pane(
            [
                sg.Column(left_section, expand_x=True, expand_y=True),
                sg.Column(right_section, expand_x=True, expand_y=True)
            ],
            orientation='horizontal',
            relief=sg.RELIEF_GROOVE,
            expand_x=True,
            expand_y=True,
            show_handle=True,
            key='-MAIN-PANE-'
        )]
    ]

    window = sg.Window('Database Browser', layout, resizable=True, finalize=True, size=(1800, 900))
    
    # Bind keyboard shortcuts (lowercase)
    # We add multiple variants to ensure they work across different OS/backend versions
    for char in ['p', 'g', 'q', 's', 'r']:
        window.bind(f'<Alt-{char}>', f'ALT-{char.upper()}')
        window.bind(f'<Alt-{char.upper()}>', f'ALT-{char.upper()}')

    
    # Update history dropdown
    window['-QUERY-HISTORY-'].update(values=query_history_list)
    
    # Show default query results on startup
    update_table(browser.default_query)

    while True:
        event, values = window.read()
        
        # Debug: print event for hotkey testing
        if isinstance(event, str) and event.startswith('ALT-'):
            logger.debug(f"Hotkey triggered: {event}")
        
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        elif event == 'Export DB':
            export_path = sg.popup_get_file('Save database as...', save_as=True, default_extension='.db', file_types=(('SQLite DB', '*.db'),))
            if export_path:
                try:
                    shutil.copy('database.db', export_path)
                    logger.debug(f"Database exported to {export_path}")
                    sg.popup('Database exported successfully!', title='Export')
                except Exception as e:
                    sg.popup(f'Export failed: {e}', title='Export Error')
                    logger.debug(f"Export failed: {e}")
                    
        elif event == 'Import DB':
            import_path = sg.popup_get_file(
                'Select SQLite database to import',
                file_types=(('SQLite DB', '*.db;*.sqlite;*.sqlite3'),)
            )
            if import_path:
                try:
                    logger.debug(f"Importing database from {import_path}")
                    sg.popup('Database imported successfully! Run a query to see data.', title='Import')

                    browser.engine = create_engine(f'sqlite:///{import_path}', echo=False)
                    browser.current_page = 0
                except Exception as e:
                    sg.popup(f'Import failed: {e}', title='Import Error')
        elif event == '-RESET-':
            # Save current state before resetting
            current_query = values['-QUERY-'].strip()
            current_prompt = values['-AI-PROMPT-'].strip()
            
            # Save to history if there's meaningful content
            if current_query and current_query != browser.default_query:
                history_entry = {
                    'prompt': current_prompt if current_prompt else '',
                    'query': current_query,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Add to history (avoid duplicates)
                if not query_history_data or query_history_data[0]['query'] != current_query:
                    query_history_data.insert(0, history_entry)
                    query_history_data = query_history_data[:MAX_HISTORY]
                    save_history(query_history_data)
                    query_history_list = [item['query'] for item in query_history_data]
                    window['-QUERY-HISTORY-'].update(values=query_history_list)
            
            # Reset everything
            browser.current_page = 0
            window['-QUERY-'].update(browser.default_query)
            window['-AI-PROMPT-'].update('')  # Clear AI prompt
            # Clear table
            window['-TABLE-'].update(values=[])
            window['-TABLE-INFO-'].update('')
            window['-PAGE_INFO-'].update('')
        elif event == '-SEARCH-' or event == 'ALT-S':
            browser.current_page = 0
            query = values['-QUERY-'].strip()
            prompt = values['-AI-PROMPT-'].strip()
            if query:
                # Create history entry with prompt and query
                history_entry = {
                    'prompt': prompt if prompt else '',  # Save empty string if no prompt
                    'query': query,
                    'timestamp': datetime.now().isoformat()
                }
                
                logger.debug(f"Saving history entry: prompt='{prompt}', query='{query[:50]}...'")
                
                # Check for duplicate by query only
                is_duplicate = False
                for existing in query_history_data:
                    if existing['query'] == query:
                        is_duplicate = True
                        break
                
                # Add to history data only if unique
                if not is_duplicate:
                    query_history_data.insert(0, history_entry)
                    query_history_data = query_history_data[:MAX_HISTORY]  # Keep max 300
                    save_history(query_history_data)
                    # Update dropdown
                    query_history_list = [item['query'] for item in query_history_data]
                    window['-QUERY-HISTORY-'].update(values=query_history_list, value=query)
                
                # Execute query and show results in table
                update_table(query)
        
        elif event == '-QUERY-HISTORY-':
            # Load selected query from history
            selected_query = values['-QUERY-HISTORY-']
            if selected_query:
                # Find the history entry
                for entry in query_history_data:
                    if entry['query'] == selected_query:
                        window['-QUERY-'].update(entry['query'])
                        if entry.get('prompt'):
                            window['-AI-PROMPT-'].update(entry['prompt'])
                        break
        
        elif event == '-COPY-CSV-':
            copy_table_to_csv()
        elif event == '-GENERATE-SQL-' or event == 'ALT-G':
            # Use saved API settings from config
            prompt = values['-AI-PROMPT-'].strip()
            api_key = config.get('api_key', '')
            model = config.get('model', 'z-ai/glm-4.7-flash')
            
            if not prompt:
                sg.popup_error('Please enter a prompt describing what you want to query.')
                continue
            
            if not api_key:
                sg.popup_error('Please configure API settings first.\nGo to: AI → LLM Settings')
                continue
            
            # Save current query and prompt before generating new SQL
            current_query = values['-QUERY-'].strip()
            current_prompt_old = values['-AI-PROMPT-'].strip()
            
            if current_query and current_query != browser.default_query:
                history_entry = {
                    'prompt': current_prompt_old if current_prompt_old else '',
                    'query': current_query,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Check for duplicate
                is_duplicate = False
                for existing in query_history_data:
                    if existing['query'] == current_query:
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    query_history_data.insert(0, history_entry)
                    query_history_data = query_history_data[:MAX_HISTORY]
                    save_history(query_history_data)
                    query_history_list = [item['query'] for item in query_history_data]
                    window['-QUERY-HISTORY-'].update(values=query_history_list)
            
            # Generate SQL
            schema = browser.get_schema()
            sql_result = generate_sql_with_ai(prompt, model, api_key, schema)
            
            # Auto-apply to query editor if successful
            if sql_result and not sql_result.startswith('Error:'):
                window['-QUERY-'].update(sql_result)
                sg.popup_quick_message('SQL generated and applied to query editor!', background_color='green', text_color='white')
            else:
                sg.popup_error(f'Failed to generate SQL:\n{sql_result}')
        
        # Keyboard shortcut for AI prompt focus
        elif event == 'ALT-P':
            window['-AI-PROMPT-'].set_focus()
            continue
        
        elif event == 'LLM Settings...':
            open_ai_settings()
        
        elif event in THEMES:
            # Theme selected from menu - save and restart to apply immediately
            config['theme'] = event
            save_config(config)
            sg.popup_quick_message(f'Changing theme to {event}... Restarting...', background_color='red', text_color='white')
            # Restart using -m to preserve package context for relative imports
            os.execl(sys.executable, sys.executable, '-m', 'freesimplesql')
        
        # Keyboard shortcut for SQL Query focus
        elif event == 'ALT-Q':
            window['-QUERY-'].set_focus()
            continue
        
        elif event == '-FIRST-':
            browser.current_page = 0
            update_table(values['-QUERY-'].strip())
        elif event == '-PREVIOUS-':
            if browser.current_page > 0:
                browser.current_page -= 1
                update_table(values['-QUERY-'].strip())
        elif event == '-NEXT-':
            if (browser.current_page + 1) * browser.page_size < browser.total_rows:
                browser.current_page += 1
                update_table(values['-QUERY-'].strip())
        elif event == '-LAST-':
            browser.current_page = (browser.total_rows - 1) // browser.page_size
            update_table(values['-QUERY-'].strip())
        elif event == '-TABLE-':
            if values['-TABLE-']:
                selected_idx = values['-TABLE-'][0]
                if selected_idx < len(current_page_rows):
                    row = current_page_rows[selected_idx]
                    # Handle both Message objects and dictionaries
                    if isinstance(row, dict):
                        row_dict = row
                    else:
                        row_dict = {col: getattr(row, col, '') for col in current_columns}
                    # Try to parse msg_content if it exists
                    if 'msg_content' in row_dict and row_dict['msg_content'] is not None:
                        try:
                            parsed_content = json.loads(row_dict['msg_content'])
                            row_dict['msg_content'] = parsed_content
                        except (json.JSONDecodeError, TypeError):
                            logger.debug("Failed to parse msg_content as JSON.")
                    # Update both JSON and Plain Text tabs
                    pretty_json = json.dumps(row_dict, indent=4, default=str)
                    plain_text = '\n'.join([f"{k}: {v}" for k, v in row_dict.items()])
                    window['-DETAIL-JSON-'].update(pretty_json)
                    window['-DETAIL-PLAIN-'].update(plain_text)
                else:
                    logger.debug("Selected index is out of range for the query result.")


    window.close()

if __name__ == "__main__":
    main()

