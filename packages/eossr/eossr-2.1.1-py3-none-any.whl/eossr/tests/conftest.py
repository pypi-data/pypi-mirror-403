import os
from pathlib import Path

from dotenv import load_dotenv


def pytest_configure():
    env_variables_file = Path(__file__).parent.joinpath("../../tokens.env").resolve()

    if os.path.exists(env_variables_file):
        print(f"Loading tokens from {env_variables_file}")
        load_dotenv(env_variables_file, override=True)


pytest_configure()
