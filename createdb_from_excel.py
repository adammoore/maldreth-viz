import os
import sqlite3
import pandas as pd
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database and Excel file paths
DB_FILE = 'research_data_lifecycle.db'
EXCEL_FILE = 'research_data_lifecycle.xlsx'

def is_uppercase(s):
    return s.isupper()

def initialize_database_from_excel(excel_file, db_file):
    if os.path.exists(db_file):
        os.remove(db_file)
        logging.info(f"Deleted existing database: {db_file}")

    conn = None
    try:
        conn = sqlite3.connect(db_file)
        logging.info(f"Created new database: {db_file}")

        # Create tables
        conn.executescript('''
            CREATE TABLE IF NOT EXISTS LifeCycle (
                stage TEXT PRIMARY KEY,
                stagedesc TEXT
            );

            CREATE TABLE IF NOT EXISTS SubStage (
                substagename TEXT,
                substagedesc TEXT,
                exemplar TEXT,
                stage TEXT,
                FOREIGN KEY (stage) REFERENCES LifeCycle(stage)
            );

            CREATE TABLE IF NOT EXISTS Tools (
                ToolName TEXT,
                ToolDesc TEXT,
                ToolLink TEXT,
                ToolProvider TEXT,
                stage TEXT,
                FOREIGN KEY (stage) REFERENCES LifeCycle(stage)
            );

            CREATE TABLE IF NOT EXISTS CycleConnects (
                id INTEGER PRIMARY KEY,
                start TEXT,
                end TEXT,
                type TEXT
            );
        ''')
        logging.info("Tables created successfully.")

        sheets = pd.read_excel(excel_file, sheet_name=None)
        data_frames = {}
        for sheet_name in sheets.keys():
            if sheet_name == 'Tool categories and description':
                header_row = 0
            elif is_uppercase(sheet_name):
                header_row = 6
            else:
                continue

            if len(sheets[sheet_name]) > header_row:
                data_frames[sheet_name] = pd.read_excel(excel_file, sheet_name=sheet_name, header=header_row)
                data_frames[sheet_name].columns = [col.strip().replace('\n', '').replace('  ', '') for col in data_frames[sheet_name].columns]
            else:
                logging.warning(f"Skipping sheet {sheet_name} as it does not have enough rows.")

        df_stage = data_frames.get('Tool categories and description')
        if df_stage is not None:
            lifecycle_data = df_stage['RESEARCH DATA LIFECYCLE STAGE'].unique()
            for stage in lifecycle_data:
                conn.execute("INSERT OR REPLACE INTO LifeCycle (stage, stagedesc) VALUES (?, ?)", (stage, df_stage[df_stage['RESEARCH DATA LIFECYCLE STAGE'] == stage]['DESCRIPTION (1 SENTENCE)'].iloc[0]))
            logging.info(f"Inserted {len(lifecycle_data)} lifecycle stages.")

            for _, row in df_stage.iterrows():
                conn.execute("""
                    INSERT OR REPLACE INTO SubStage (substagename, substagedesc, exemplar, stage) 
                    VALUES (?, ?, ?, ?)
                """, (row['TOOL CATEGORY TYPE'], row['DESCRIPTION (1 SENTENCE)'], row['EXAMPLES'], row['RESEARCH DATA LIFECYCLE STAGE']))

        for sheet_name, df_tools in data_frames.items():
            if sheet_name == 'Tool categories and description':
                continue

            required_columns = {'TOOL CHARACTERISTICS (ADDITIONAL USEFUL INFORMATION)', 'LINK TO TOOL (URL)', 'TOOL PROVIDER (NAME)'}
            if not required_columns.issubset(df_tools.columns):
                logging.warning(f"Skipping sheet {sheet_name} as it does not have the required columns.")
                continue

            stage = sheet_name.strip()
            for _, row in df_tools.iterrows():
                tools = row['TOOL NAME']
                if isinstance(tools, str):
                    for tool in tools.split(','):
                        conn.execute("""
                            INSERT OR REPLACE INTO Tools (ToolName, ToolDesc, ToolLink, ToolProvider, stage) 
                            VALUES (?, ?, ?, ?, ?)
                        """, (tool.strip(), row['TOOL CHARACTERISTICS (ADDITIONAL USEFUL INFORMATION)'], row['LINK TO TOOL (URL)'], row['TOOL PROVIDER (NAME)'], stage))

        # Populate CycleConnects
        cycle_connects_data = [
            (1, 1, 2, 'normal'),
            (2, 2, 3, 'normal'),
            (3, 3, 4, 'normal'),
            (4, 4, 5, 'normal'),
            (5, 5, 6, 'normal'),
            (6, 6, 7, 'normal'),
            (7, 7, 8, 'normal'),
            (8, 8, 9, 'normal'),
            (9, 9, 10, 'normal'),
            (10, 10, 11, 'normal'),
            (11, 11, 12, 'normal'),
            (12, 12, 1, 'normal'),
            (13, 3, 4, 'alternative'),
            (14, 4, 5, 'alternative'),
            (15, 5, 6, 'alternative')
        ]

        conn.executemany("INSERT INTO CycleConnects (id, start, end, type) VALUES (?, ?, ?, ?)", cycle_connects_data)
        logging.info(f"Inserted {len(cycle_connects_data)} cycle connections.")

        conn.commit()
        logging.info("Database initialized from Excel file.")
    except (sqlite3.Error, pd.errors.EmptyDataError, KeyError) as e:
        logging.error(f"Error initializing database: {e}")
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    initialize_database_from_excel(EXCEL_FILE, DB_FILE)
