"""Command-line interface for MaxQuery"""
import sys
import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from maxquery.core import MaxQueryRunner
from maxquery.credentials import CredentialsManager

console = Console()


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """🚀 MaxQuery - MaxCompute Query Runner
    
    Execute SQL queries on Alibaba Cloud MaxCompute (ODPS) from the command line.
    """
    pass


@cli.command()
@click.option(
    '--setup',
    is_flag=True,
    help='Interactive setup of MaxCompute credentials'
)
@click.option(
    '--access-id',
    prompt=False,
    help='MaxCompute Access ID'
)
@click.option(
    '--access-key',
    prompt=False,
    help='MaxCompute Access Key'
)
@click.option(
    '--project',
    prompt=False,
    help='MaxCompute Project Name'
)
@click.option(
    '--endpoint',
    default='http://service.odps.aliyun.com/api',
    help='MaxCompute Endpoint'
)
@click.option(
    '--region',
    default='ap-southeast-5',
    help='Region for endpoint'
)
@click.option(
    '--show',
    is_flag=True,
    help='Show current credentials'
)
@click.option(
    '--delete',
    is_flag=True,
    help='Delete saved credentials'
)
def config(setup, access_id, access_key, project, endpoint, region, show, delete):
    """Manage MaxCompute credentials
    
    Examples:
        maxquery config --setup              # Interactive setup
        maxquery config --show               # Show current credentials
        maxquery config --delete             # Delete saved credentials
    """
    if delete:
        CredentialsManager.delete_credentials()
        return
    
    if show:
        creds = CredentialsManager.load_credentials()
        if creds:
            creds_table = Table(title="📋 Saved Credentials", box=None)
            creds_table.add_column("Key", style="magenta")
            creds_table.add_column("Value", style="green")
            creds_table.add_row("Project", creds.get('project', 'N/A'))
            creds_table.add_row("Region", creds.get('region', 'N/A'))
            creds_table.add_row("Access ID", creds.get('access_id', 'N/A')[:15] + "...")
            console.print(creds_table)
        else:
            console.print("[red]❌ No credentials saved[/red]")
            console.print("[yellow]Run:[/yellow] [bold]maxquery config --setup[/bold]")
        return
    
    if setup or not (access_id and access_key and project):
        # Interactive setup
        console.print("\n[bold cyan]🔐 MaxCompute Credentials Setup[/bold cyan]")
        console.print("[dim]" + "="*40 + "[/dim]\n")
        
        access_id = click.prompt("  Access ID")
        access_key = click.prompt("  Access Key", hide_input=True)
        project = click.prompt("  Project Name")
        endpoint = click.prompt("  Endpoint", default=endpoint)
        region = click.prompt("  Region", default=region)
    
    CredentialsManager.save_credentials(
        access_id=access_id,
        access_key=access_key,
        project=project,
        endpoint=endpoint,
        region=region
    )


@cli.command()
@click.argument('sql_files', nargs=-1, required=True, type=click.Path(exists=True))
@click.option(
    '--format',
    type=click.Choice(['1', '2']),
    default='1',
    help='Output format: 1=CSV (default), 2=Parquet'
)
@click.option(
    '--output',
    '-o',
    default='outputs',
    help='Output directory (default: outputs)'
)
@click.option(
    '--no-download',
    is_flag=True,
    help='Run queries but keep results in memory (don\'t save files)'
)
def run(sql_files, format, output, no_download):
    """Execute SQL query files
    
    Examples:
        maxquery run queries/my_query.sql
        maxquery run queries/*.sql --format 2
        maxquery run query1.sql query2.sql -o results/
        maxquery run query.sql --no-download
    """
    if not CredentialsManager.has_credentials():
        click.echo("❌ Error: No credentials configured")
        click.echo("   Run: maxquery config --setup")
        sys.exit(1)
    
    runner = MaxQueryRunner(output_dir=output)
    runner.run_queries(
        sql_files=sql_files,
        output_format=format,
        download=not no_download
    )


@cli.command()
def info():
    """Show configuration and credentials info"""
    import os
    
    # Create info table
    info_data = []
    info_data.append(["📦 Package", "MaxQuery"])
    info_data.append(["📌 Version", "1.0.0"])
    info_data.append(["👨‍💻 Author", "Chethan Patel"])
    info_data.append(["📧 Email", "chethanpatel100@gmail.com"])
    info_data.append(["🔗 GitHub", "github.com/chethanpatel/maxquery"])
    
    table = Table(title="MaxQuery Configuration", show_header=False, box=None)
    for row in info_data:
        table.add_row(row[0], row[1], style="cyan")
    
    console.print(table)
    console.print()
    
    # Check credentials
    creds = CredentialsManager.load_credentials()
    if creds:
        creds_table = Table(title="Credentials", box=None)
        creds_table.add_column("Key", style="magenta")
        creds_table.add_column("Value", style="green")
        creds_table.add_row("Project", creds.get('project', 'N/A'))
        creds_table.add_row("Region", creds.get('region', 'N/A'))
        creds_table.add_row("Endpoint", creds.get('endpoint', 'N/A')[:50] + "...")
        console.print(creds_table)
    else:
        console.print("[red]❌ No saved credentials[/red]")
        console.print("[yellow]Run:[/yellow] [bold]maxquery config --setup[/bold]")
    
    console.print()


def main():
    """Entry point for CLI"""
    cli()


if __name__ == '__main__':
    main()
