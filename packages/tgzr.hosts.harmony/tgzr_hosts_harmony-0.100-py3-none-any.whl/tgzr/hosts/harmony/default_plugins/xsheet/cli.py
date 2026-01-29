import click


def install_in_group(group: click.Group):
    group.add_command(xsheet_cli)


@click.group(name="xsheet", help="xsheet plugin cli tools")
def xsheet_cli():
    pass


@xsheet_cli.command
@click.option(
    "-s", "--stage", required=True, help="Path of the harmony xstage to process."
)
@click.option("-o", "--output", required=True, help="Path of the xsheet to save.")
def export(stage: str, output: str):
    click.echo(f"Opening stage {stage!r}")
    click.echo(f"Exporting xsheet {output!r}")
    click.echo("Just kidding, this is just a plugin demo...")
