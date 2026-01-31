from dataclasses import dataclass
from typing import List


@dataclass
class EnvironmentConfig:
    console_enabled: bool
    file_enabled: bool
    file_reset_on_start: bool
    error_file_enabled: bool
    error_file_reset_on_start: bool
    slack_enabled: bool
    slack_levels: List[str]
    github_enabled: bool
    storage_enabled: bool


def get_environment_config(environment: str) -> EnvironmentConfig:
    configs = {
        "development": EnvironmentConfig(
            console_enabled=True,
            file_enabled=True,
            file_reset_on_start=True,
            error_file_enabled=True,
            error_file_reset_on_start=True,
            slack_enabled=False,
            slack_levels=[],
            github_enabled=False,
            storage_enabled=False
        ),
        "staging": EnvironmentConfig(
            console_enabled=True,
            file_enabled=True,
            file_reset_on_start=True,
            error_file_enabled=True,
            error_file_reset_on_start=True,
            slack_enabled=True,
            slack_levels=["critical"],
            github_enabled=False,
            storage_enabled=True
        ),
        "production": EnvironmentConfig(
            console_enabled=True,
            file_enabled=True,
            file_reset_on_start=True,
            error_file_enabled=True,
            error_file_reset_on_start=True,
            slack_enabled=True,
            slack_levels=["error", "critical"],
            github_enabled=True,
            storage_enabled=True
        )
    }
    return configs.get(environment, configs["development"])
