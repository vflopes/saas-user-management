# SaaS User Management

This application is designed to manage users for a Software as a Service (SaaS) platform. It provides functionalities for user registration, authentication, profile management, and role-based access control.

## Project Structure

- `src/`: Contains the source code for the application.
  - `controllers/`: Handles incoming requests and responses, this is where the main logic for each endpoint resides (like AWS Lambda handlers).
  - `adapters/`: Interfaces with external services or databases.
  - `facades/`: Provides simplified interfaces to complex subsystems (like multi-step processes).
  - `services/`: Contains business logic and interacts with models.
  - `dto/`: Data Transfer Objects for validating and transferring data.
  - `validators/`: Contains validation logic for data.
  - `settings.py`: Configuration settings for the application (uses Pydantic Settings)

## Commands

Poetry is used for dependency management and virtual environments. To run any command within the project's virtual environment, use:

```bash
poetry run <command>
```

## Libraries and Frameworks Used

- **boto3**: AWS SDK for Python, used for interacting with AWS services.
- **aws-lambda-powertools**: A suite of utilities for AWS Lambda functions to ease the adoption of best practices such as structured logging, tracing, and metrics.
- **pydantic**: Data validation and settings management using Python type annotations.
- **pydantic-settings**: Extension of Pydantic for managing application settings.
- **saas-python-lib**: A library providing common functionalities for SaaS applications.

## Linting and Testing

Linting is done using `ruff`, ensuring code quality and adherence to coding standards. To run linting, use the following command:

```bash
poetry run ruff check .
```

Testing is performed using the standard library `unittest`. To run tests, use the following command:

```bash
poetry run  python -m unittest discover -s src -p "*_test.py"
```

Test files are located alongside the source code files, following the naming convention `*_test.py`.

- Don't over-engineer the `saas-python-lib`, just mock it using `@patch` and `Mock/MagicMock`.

## Infrastructure as Code

Terraform is used for managing infrastructure as code. The Terraform configuration files are located in the `env/production/` directory. This setup allows for easy deployment and management of AWS resources required by the application.
