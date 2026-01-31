import typer
from pathlib import Path
from dddify.service import DDDGenerator
from dddify.config import DDDifyConfig

app = typer.Typer()


def _generate_structure(
    domain: str,
    entity: str = None,
    output: str = None
):
    if entity is None:
        entity = domain
    
    config = DDDifyConfig.load()
    output_path = Path(output) if output else Path(config.output_dir)
    
    templates_dir = Path(__file__).parent / "templates"
    
    generator = DDDGenerator(templates_dir)
    generator.generate(domain, entity, output_path)


@app.command()
def generate(
    domain: str = typer.Argument(..., help="Domain name"),
    entity: str = typer.Argument(None, help="Entity name"),
    output: str = typer.Option(None, "-o", "--output", help="Output directory (overrides config)")
):
    _generate_structure(domain, entity, output)


@app.command()
def g(
    domain: str = typer.Argument(..., help="Domain name"),
    entity: str = typer.Argument(None, help="Entity name"),
    output: str = typer.Option(None, "-o", "--output", help="Output directory (overrides config)")
):
    _generate_structure(domain, entity, output)