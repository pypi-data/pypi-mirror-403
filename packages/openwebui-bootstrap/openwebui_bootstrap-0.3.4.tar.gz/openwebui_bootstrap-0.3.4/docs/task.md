# Task description

Your task is to create a python library and commandline tool to bootstrap a deployment of Open Webui by directly writing configuration
into the Open-Webui Database.

The commandline tool should be called with a configuration file (see example-config.yaml for initial structure) and an option --reset which clears the database completely before running the script. If --reset is not available, it should only update existing data in the database or add new one.

- You will find a copy of this task in docs/task.md
- You will find a reference of the sqlite database structure at docs/webui_database_reference.txt
- You will find a real databse in resources/webui.db. You can get *read only* access to this database as reference for implementations

## Your task is:

1. Set up a basic project structure which follows python best practice
2. Create a comprehensive readme.md which describes the project and prepare a changelog.txt
3. Create the data models for the project. You will find example-config-yaml, which gives you an initial structure of the configuration
4. Create a database interface class, that will access the Open WebUI configuration database. The initially supported database is sqlite, but prepare the interface to add support for different databases later (create an abstract base class)
5. Create a support module, which you can use to read only access the reference database 'resources/webui.db'. Use the helper modeul to test your implementation during development
6. Create a configuration manager class, that reads in the configuration file and uses the database interface to modify the database
7. The configuration manager should be able to upsert datasets and to remove all data from tables in the database
8. You are allowed to adopt the example file to fit the needs of the project and to match with the webui database structure
9. Once you finalized a first draft, create a comprehensive set of pytest cases. Ensure that all tests pass
10. Run pytest coverage to ensure that you get best coverage


# Testing

- Prepare a comprehensive set of test cases using pytest
- Run coverage to achieve a coverage of at least 85%
- Create a re-usable test fixture in a separate file, which generates an sqlite test database, so there is no need to run on a real database. After teardoen the database should be deleted.

# Project guidelines:

- The friendly name (for docs) is Open WebUI Bootstrap.
- The package name is openwebui_bootstrap
- Python tests should reside in folder 'tests' in the workspace
- This project is licensed under MIT license
- python version is >= 3.13
- Use uv as package manager
- To run python command you must prefix with 'uv run' to enable the venv
- Usd 'uv add' to install new packages, and remove to uninstall them 
- use 'uv add --dev' to install a development package that is not used in production
- If python acces fails, try 'uv sync --dev' first
- Add a confiuguration for ruff and package building in pyproject.toml

