# LogAssist

A simple and customizable logging library for Python.

## Installation

```powershell
pip install LogAssist
```

## Features

-   Easy to use and configure
-   Supports multiple log levels (debug, info, warning, error)
-   Outputs log messages to both console and file
-   Allows for log file removal on initialization
-   Provides datetime formatting for log messages

## Usage

1. Import the Logger class:

```python
import LogAssist.log as Logger
```

2. Initialize the logger with your desired settings:

```python
Logger.logger_init(config=my_config_dictionary)
# or
Logger.logger_init()
```

3. Use the logger in your code:

```python
Logger.verbose('MyTag', 'This is a verbose message')
Logger.debug('MyTag', 'This is a debug message')
Logger.info('MyTag', 'This is an info message')
Logger.warn('MyTag', 'This is a warning message')
Logger.error('MyTag', 'This is an error message')
Logger.exception('MyTag', 'This is a exception message')
```

## Configuration

You can configure the logger using a JSON configuration. Below is an example of a configuration and explanations for each field.

Example Usage:

```json
{
    "base": {
        "name": "MyLogger",
        "level": "debug"
    },
    "console": {
        "level": "debug",
        "format": "%(asctime)s[%(levelname)s]%(message)s"
    },
    "file_timed": {
        "level": "info",
        "format": "%(asctime)s[%(levelname)s]%(message)s",
        "file_name": "default.log",
        "when": "midnight",
        "interval": 1,
        "backup_count": 30
    }
}
```

## Configuration Fields

### base

-   name: The identifier for the logger. Default is 'MyLogger'.
-   level: The minimum log level to set (debug, info, warn, error, exception). Default is 'debug'.

### console

-   level: The minimum log level for console output (debug, info, warn, error, exception). Default is 'debug'.
-   format: Defines the log message format for console output. Default is %(asctime)s[%(levelname)s]%(message)s.

### file_timed

-   level: The minimum log level for file output (debug, info, warn, error, exception). Default is 'info'.
-   format: Defines the log message format for file output. Default is %(asctime)s[%(levelname)s]%(message)s.
-   file_name: The file name to use for logging. Default is 'default.log'.
-   when: The time interval for rotating the log file (e.g., 'midnight'). Default is 'midnight'.
-   interval: Defines how often the log file is rotated. Default is 1.
-   backup_count: Specifies the number of backup files to keep. Default is 30.

Use this JSON configuration to initialize your logger with the desired settings.
