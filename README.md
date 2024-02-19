# Twidder

This project was developed as a part of the Web Programming (TDDD97) course at [Linköping University](https://liu.se/).

The project presents an HTML5 Single-page application with Python backend and SQLite database.

## Prerequisites

- Linux OS
- Python 3.10
- Python packages listed in `requirements.txt`
    - Install with: ```pip install -r requirements.txt```
- Gunicorn
    - See [Installation instructions](https://docs.gunicorn.org/en/stable/install.html)

## Run tests

- Run tests by running ```pytest``` in the root folder of this repository

## Run project

- Run the server using one of the following commands:
    - ```python3 ./appserver.py``` for development
    - ```./run.sh``` for production
- Access the application on http://localhost:8080/
