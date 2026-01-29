from pydantic import Field
from pydantic_settings import BaseSettings, CliSubCommand, get_subcommand

from webquest_mcp.app import AppSettings, run_app
from webquest_mcp.token_generator import TokenGeneratorSettings, generate_token


class Settings(BaseSettings, cli_parse_args=True):
    run: CliSubCommand[AppSettings] = Field(default=...)
    token: CliSubCommand[TokenGeneratorSettings] = Field(default=...)


def main(settings: Settings | None = None) -> None:
    settings = settings or Settings()
    subcommand = get_subcommand(settings)
    if isinstance(subcommand, AppSettings):
        run_app(settings=settings.run)
    elif isinstance(subcommand, TokenGeneratorSettings):
        generate_token(settings=settings.token)


if __name__ == "__main__":
    main()
