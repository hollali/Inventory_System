# Inventory Management System

## Overview
The Inventory Management System is a robust and flexible application designed to streamline the tracking and management of inventory. This system supports both MySQL and SQLite databases, offering versatility for different deployment environments. It is built using Python, leveraging its powerful libraries to ensure a reliable and efficient application.

## Features
- **Multi-Database Support**: Easily switch between MySQL and SQLite for backend storage.
- **User-Friendly Interface**: Simplified command-line interface for easy navigation and operation.
- **CRUD Operations**: Full create, read, update, and delete functionality for inventory items.
- **Report Generation**: Generate reports on inventory levels, transactions, and more.
- **Transaction Logging**: Maintain an audit trail of all changes made to the inventory.

## Requirements
- Python 3.8+
- MySQL 8.0+ (optional for MySQL support)
- SQLite 3.0+ (included with Python)
- Python Libraries:
  - `mysql-connector-python`
  - `sqlite3` (built-in with Python)
  - `SQLAlchemy` (optional, for ORM support)
  - `pandas` (for data manipulation and reporting)

## Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/hollali/Inventory-System.git
   cd inventory-system
   ```

2. **Set Up Virtual Environment**
   ```bash
   python3 -m venv env
   source env/bin/activate   # On Windows use `env\Scripts\activate`
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Database Configuration**
   - **MySQL**: Create a database and update the `config.ini` file with your MySQL credentials.
   - **SQLite**: No additional setup needed, the SQLite database will be created automatically.

## Configuration
Update the `config.ini` file to specify the database settings.

```ini
[database]
engine = mysql    # Change to 'sqlite' for SQLite database
host = localhost
user = yourusername
password = yourpassword
database = inventory_db
```

## Usage

1. **Run the Application**
   ```bash
   python dashboard.py
   ```

2. **Basic Commands**
   - `add`: Add a new item to the inventory.
   - `list`: List all items in the inventory.
   - `update`: Update details of an existing item.
   - `delete`: Remove an item from the inventory.
   - `report`: Generate a report of current inventory levels.

3. **Database Migration**
   - For MySQL:
     ```bash
     python manage.py migrate --db mysql
     ```
   - For SQLite:
     ```bash
     python manage.py migrate --db sqlite
     ```

## Development

1. **Testing**
   - Run tests using `unittest` or `pytest` frameworks.
   ```bash
   python -m unittest discover tests
   ```

2. **Code Style**
   - Follow PEP 8 standards. Use tools like `flake8` for linting.

## Contributing
Contributions are welcome! Please read the [CONTRIBUTING.md](CONTRIBUTING.md) file for more information on how to contribute to this project.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.

## Acknowledgements
- Python
- MySQL
- SQLite
- Community contributors
```

This `README.md` provides a comprehensive guide for users and contributors, covering setup, usage, and contribution details. Adjust the sections to fit the specifics of your project.