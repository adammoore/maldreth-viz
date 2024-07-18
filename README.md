# MaLDReTH: Research Data Lifecycle Management Visualization

This project provides an interactive visualization tool for the Research Data Lifecycle, implemented using Dash and SQLite. It's part of the MaLDReTH (Managing Lifecycle of Data Resources and Theses) project.

## Features

- Interactive graph visualization of the Research Data Lifecycle stages
- Detailed information on substages for each lifecycle stage
- Tool management system for each stage of the lifecycle
- Responsive design for various screen sizes
- SQLite database for storing and managing lifecycle data
- Support for alternative paths in the lifecycle

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
- `initialize_database.py`: Script to initialize the database with initial data
- `requirements.txt`: List of Python package dependencies

## Database Schema

The SQLite database contains the following tables:

1. `LifeCycle`: Stores information about each stage of the research data lifecycle
   - Columns: rowid, stage, stagedesc

2. `SubStage`: Contains details about substages within each lifecycle stage
   - Columns: substagename, substagedesc, stage

3. `Tools`: Stores information about tools associated with each stage
   - Columns: ToolName, ToolDesc, ToolLink, ToolProvider, stage

4. `CycleConnects`: Defines the connections between lifecycle stages
   - Columns: id, start, end, type

## Features in Detail

### Lifecycle Visualization

- The main view displays a circular graph representing the Research Data Lifecycle stages.
- Each stage is represented by a node in the graph.
- Connections between stages are shown as edges, with alternative paths displayed as dashed lines.

### Stage Details

- Clicking on a stage node displays detailed information about that stage.
- Substages are shown in both graphical and text views.
- Associated tools for the selected stage are listed in a table.

### Tool Management

- Users can add, edit, and delete tools associated with each stage.
- Tool information includes name, description, link, and provider.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- This project is part of the MaLDReTH initiative.
- Thanks to all contributors and users of this visualization tool.

## Contact

For any queries or further information, please contact [Your Name] at [your.email@example.com].