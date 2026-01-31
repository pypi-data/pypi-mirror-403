from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from rich.console import Console
from rich.tree import Tree
from rich.panel import Panel
from rich.prompt import Confirm

from dddify.utils import to_pascal_case, to_snake_case

console = Console()


class DDDGenerator:
    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def generate(self, domain_name: str, entity_name: str, output_dir: Path) -> None:
        context = self._build_context(domain_name, entity_name, output_dir)
        target_dir = output_dir / context['domain_slug']

        if target_dir.exists():
            console.print()
            console.print(f"[yellow]⚠[/yellow]  Directory [cyan]{target_dir}[/cyan] already exists!")
            
            if not Confirm.ask("Do you want to overwrite?", default=False):
                console.print("[red]✗[/red] Cancelled")
                return
            
            console.print()
        structure = self._get_structure()
        
        self._print_header(context)
        tree, file_count = self._generate_files(context, structure, output_dir)
        self._print_summary(tree, file_count, output_dir, context['domain_slug'])
    
    def _build_context(self, domain_name: str, entity_name: str, output_dir: Path) -> dict[str, str]:
        domain_slug = to_snake_case(domain_name)
        entity_slug = to_snake_case(entity_name)
        entity_pascal = to_pascal_case(entity_name)
        domain_pascal = to_pascal_case(domain_name)
        
        base_module = self._calculate_base_module(output_dir)
        domain_path = f"{base_module}.{domain_slug}" if base_module else domain_slug
        
        return {
            'domain_name': domain_name,
            'domain_pascal': domain_pascal,
            'domain_slug': domain_slug,
            'entity_name': entity_pascal,
            'entity_name_lower': entity_slug,
            'value_object_name': f"{entity_pascal}Id",
            'table_name': f"{entity_slug}s",
            'api_prefix': f"/{entity_slug}s",
            'base_module': base_module,
            'domain_path': domain_path,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _calculate_base_module(self, output_dir: Path) -> str:
        """Convert output directory path to Python module path"""
        output_dir = output_dir.resolve()
        cwd = Path.cwd().resolve()
        
        # If output_dir is current directory or ".", no base module
        if output_dir == cwd or str(output_dir) == ".":
            return ""
        
        # Try to get relative path from cwd
        try:
            rel_path = output_dir.relative_to(cwd)
            # Convert path to module notation (e.g., "backend/domains" -> "backend.domains")
            return ".".join(rel_path.parts)
        except ValueError:
            # If not relative to cwd, use absolute parts
            return ".".join(output_dir.parts)
    
    def _get_structure(self) -> dict[str, list[tuple[str, str | None]]]:
        return {
            'domain': [
                ('aggregate.py', 'aggregate.py.j2'),
                ('events.py', 'events.py.j2'),
                ('value_objects.py', 'value_objects.py.j2'),
                ('exceptions.py', 'exceptions.py.j2'),
                ('repo.py', 'ports.py.j2'),
                ('ports.py', 'ports_file.py.j2'),
                ('__init__.py', 'domain_init.py.j2')
            ],
            'domain/entities': [
                ('__init__.py', 'entities_init.py.j2')
            ],
            'application/commands': [
                ('__init__.py', None)
            ],
            'application/queries': [
                ('__init__.py', None)
            ],
            'application': [
                ('__init__.py', None)
            ],
            'infrastructure/persistence': [
                ('orm.py', 'orm.py.j2'),
                ('repo.py', 'repository.py.j2'),
                ('__init__.py', 'persistence_init.py.j2')
            ],
            'infrastructure/adapters': [
                ('__init__.py', None)
            ],
            'infrastructure/di': [
                ('container.py', 'container.py.j2'),
                ('__init__.py', 'di_init.py.j2')
            ],
            'presentation': [
                ('router.py', 'router.py.j2'),
                ('schemas.py', 'schemas.py.j2'),
                ('exception_handlers.py', 'exception_handlers.py.j2'),
                ('__init__.py', 'presentation_init.py.j2')
            ]
        }
    
    def _generate_files(
        self, 
        context: dict[str, str], 
        structure: dict[str, list[tuple[str, str | None]]], 
        output_dir: Path
    ) -> tuple[Tree, int]:
        """Generate all files and return tree representation and file count."""
        tree = Tree(f"[bold cyan]{context['domain_slug']}/[/bold cyan]")
        file_count = 0
        
        for directory, files in structure.items():
            dir_path = output_dir / context['domain_slug'] / directory
            dir_path.mkdir(parents=True, exist_ok=True)
            
            branch = tree.add(f"[dim cyan]{directory}/[/dim cyan]")
            
            for filename, template_name in files:
                self._create_file(dir_path / filename, template_name, context)
                self._add_to_tree(branch, filename, template_name)
                file_count += 1
        
        return tree, file_count
    
    def _create_file(self, file_path: Path, template_name: str | None, context: dict[str, str]) -> None:
        if template_name is None:
            file_path.write_text('', encoding='utf-8')
        else:
            template = self.env.get_template(template_name)
            content = template.render(**context)
            file_path.write_text(content, encoding='utf-8')
    
    def _add_to_tree(self, branch: Tree, filename: str, template_name: str | None) -> None:
        if template_name is None:
            branch.add(f"[dim]{filename}[/dim]")
        else:
            branch.add(f"[green]✓[/green] {filename}")
    
    def _print_header(self, context: dict[str, str]) -> None:
        console.print()
        console.print(Panel.fit(
            f"[bold cyan]{context['domain_name']}[/bold cyan]\n"
            f"Entity: [yellow]{context['entity_name']}[/yellow]",
            title="[bold]Generating DDD Structure[/bold]",
            border_style="cyan"
        ))
        console.print()
    
    def _print_summary(self, tree: Tree, file_count: int, output_dir: Path, domain_slug: str) -> None:
        console.print(tree)
        console.print()
        console.print(
            f"[bold green]✓[/bold green] Generated {file_count} files in [cyan]{output_dir / domain_slug}[/cyan]"
        )
        console.print()