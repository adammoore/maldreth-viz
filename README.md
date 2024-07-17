# Research Data Lifecycle Management Visualization

This project provides a interactive visualization tool for the Research Data Lifecycle, implemented using Dash and SQLite.

## Features

- Interactive graph visualization of the Research Data Lifecycle stages
- Detailed information on substages and tools for each lifecycle stage
- Responsive design for various screen sizes
- SQLite database for storing and managing lifecycle data

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/maldreth-viz.git
   cd maldreth-viz
   ```

2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Initialize the database:
   ```
   python initialize_database.py
   ```

## Usage

Run the application:

```
python main.py
```

Open a web browser and navigate to `http://localhost:8050` to view the application.

## Project Structure

- `main.py`: The main application file containing the Dash app and callbacks
- `research_data_lifecycle.db`: SQLite database file
- `research_data_lifecycle.csv`: CSV file containing initial data for the database
- `requirements.txt`: List of Python package dependencies

## Database Schema

The SQLite database contains the following tables:

1. `LifeCycle`: Stores information about each stage of the research data lifecycle
2. `SubStage`: Contains details about substages within each lifecycle stage
3. `Tools`: Stores information about tools associated with each stage
4. `CycleConnects`: Defines the connections between lifecycle stages

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.