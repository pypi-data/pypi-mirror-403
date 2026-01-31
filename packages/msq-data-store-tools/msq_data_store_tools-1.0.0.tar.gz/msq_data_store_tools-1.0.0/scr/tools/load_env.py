#!/usr/bin/env python3

import os


def load_env_file(filepath, override_existing=False):
    with open(filepath) as f:
        for line in f:
            # Strip leading/trailing whitespaces and ignore comments
            line = line.strip()
            if line and not line.startswith('#'):
                # Split the line into key and value
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")

                    # Optionally, skip overriding existing environment variables
                    if not override_existing and key in os.environ:
                        continue

                    # Set the environment variable
                    os.environ[key] = value
                else:
                    # Log or raise an error for invalid lines
                    raise ValueError(f"Invalid line in .env file: {line}")


if __name__ == '__main__':
    pass