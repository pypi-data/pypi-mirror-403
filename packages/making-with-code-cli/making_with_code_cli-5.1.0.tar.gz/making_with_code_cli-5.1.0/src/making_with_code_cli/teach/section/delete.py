import click
from making_with_code_cli.settings import read_settings
from making_with_code_cli.mwc_accounts_api import MWCAccountsAPI
from making_with_code_cli.styles import (
    address, 
    error,
    info,
    question,
)

@click.command('delete')
@click.argument("slug")
@click.option("--config", help="Path to config file (default: ~/.mwc)")
def delete_section(slug, config):
    "Delete a section"
    settings = read_settings(config)
    api = MWCAccountsAPI(settings.get('mwc_accounts_url'))
    params = {"slug": slug}
    try:
        response = api.delete_section(settings.get('mwc_accounts_token'), params)
        click.echo(info(f"Deleted section {slug}."))
    except api.RequestFailed as err:
        click.echo(error(f"Error deleting section {slug}."))

