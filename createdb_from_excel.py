import os
import sqlite3
import pandas as pd
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database and Excel file paths
DB_FILE = 'research_data_lifecycle.db'
EXCEL_FILE = 'research_data_lifecycle.xlsx'

def initialize_database_from_excel(excel_file, db_file):
    """
    Initialize the SQLite database from an Excel file.

    Args:
        excel_file (str): Path to the Excel file containing the data.
        db_file (str): Path to the SQLite database file to be created or updated.
    """
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
                start INTEGER,
                end INTEGER,
                type TEXT
            );
        ''')
        logging.info("Tables created successfully.")

        # Read Excel file
        df = pd.read_excel(excel_file)
        df.columns = [col.strip().replace('\n', '').replace('  ', '') for col in df.columns]

        # Populate lifecycle stages
        lifecycle_data = df['RESEARCH DATA LIFECYCLE STAGE'].unique()
        for stage in lifecycle_data:
            stage = stage.upper()  # Ensure stage name is uppercase to match Excel file
            conn.execute("INSERT OR REPLACE INTO LifeCycle (stage, stagedesc) VALUES (?, ?)", (stage, df[df['RESEARCH DATA LIFECYCLE STAGE'] == stage]['DESCRIPTION (1 SENTENCE)'].iloc[0]))
        logging.info(f"Inserted {len(lifecycle_data)} lifecycle stages.")

        # Populate substages and tools
        for _, row in df.iterrows():
            # Insert substage
            conn.execute("""
                INSERT OR REPLACE INTO SubStage (substagename, substagedesc, exemplar, stage) 
                VALUES (?, ?, ?, ?)
            """, (row['TOOL CATEGORY TYPE'], row['DESCRIPTION (1 SENTENCE)'], row['EXAMPLES'], row['RESEARCH DATA LIFECYCLE STAGE'].upper()))  # Convert stage to uppercase

            # Insert tools
            tools = row['EXAMPLES']
            if isinstance(tools, str):
                for tool in tools.split(','):
                    conn.execute("""
                        INSERT OR REPLACE INTO Tools (ToolName, ToolDesc, ToolLink, ToolProvider, stage) 
                        VALUES (?, ?, ?, ?, ?)
                    """, (tool.strip(), row['DESCRIPTION (1 SENTENCE)'], '', '', row['RESEARCH DATA LIFECYCLE STAGE'].upper()))  # Convert stage to uppercase

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