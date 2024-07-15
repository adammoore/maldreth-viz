import sqlite3
import pandas as pd

# Read the CSV file
csv_file = 'tools.csv'
df = pd.read_csv(csv_file)

# Connect to the SQLite database (or create it if it doesn't exist)
conn = sqlite3.connect('research_lifecycle.db')
cursor = conn.cursor()

# Create tables based on the provided schema
cursor.execute('''
    CREATE TABLE IF NOT EXISTS LifeCycle (
        stageID INTEGER PRIMARY KEY AUTOINCREMENT,
        stage TEXT,
        stagedesc TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS Tools (
        ToolID INTEGER PRIMARY KEY AUTOINCREMENT,
        ToolName TEXT,
        ToolDesc TEXT,
        ToolLink TEXT,
        stage INTEGER,
        ToolProvider TEXT,
        FOREIGN KEY(stage) REFERENCES LifeCycle(stageID)
    )
''')

# Insert data into LifeCycle table
lifecycle_data = df[['RESEARCH DATA LIFECYCLE STAGE', 'DESCRIPTION']].drop_duplicates()
lifecycle_data.columns = ['stage', 'stagedesc']
lifecycle_data.to_sql('LifeCycle', conn, if_exists='append', index=False)

# Insert data into Tools table
df = df.rename(columns={
    'RESEARCH DATA LIFECYCLE STAGE': 'stage',
    'TOOL CATEGORY TYPE ': 'ToolProvider',
    'EXAMPLES': 'ToolName',
    'DESCRIPTION': 'ToolDesc'
})
df['ToolLink'] = ''  # Add an empty ToolLink column
df = df[['ToolName', 'ToolDesc', 'ToolLink', 'stage', 'ToolProvider']]

# Map stage names to their corresponding stage IDs
stage_ids = pd.read_sql('SELECT stageID, stage FROM LifeCycle', conn)
df = df.merge(stage_ids, left_on='stage', right_on='stage')
df = df[['ToolName', 'ToolDesc', 'ToolLink', 'stageID', 'ToolProvider']]
df.columns = ['ToolName', 'ToolDesc', 'ToolLink', 'stage', 'ToolProvider']

# Insert tools data
df.to_sql('Tools', conn, if_exists='append', index=False)

conn.commit()
conn.close()
