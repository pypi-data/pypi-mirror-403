import click
import os
import shutil
import sys
from .logic import run_checks
from . import __version__

@click.group()
@click.version_option(version=__version__)
def cli():
    """LoFi Gate: Signal-first verification for AI coding agents."""
    pass

@cli.command()
@click.option('--force', is_flag=True, help="Overwrite existing files.")
def init(force):
    """Scaffold the .agent/skills/lofi-gate directory."""
    
    # 1. Resolve Paths
    # Current User Workspace (CWD)
    dest_dir = os.path.join(os.getcwd(), ".agent", "skills", "lofi-gate")
    
    # Package Templates Directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(base_dir, "templates")
    
    # 2. Create Directory
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        click.echo(f"📁 Created directory: {dest_dir}")
    
    # 3. Copy Files
    files = ["SKILL.md", "lofi.toml", "judge.py"]
    
    for filename in files:
        src = os.path.join(templates_dir, filename)
        dest = os.path.join(dest_dir, filename)
        
        if os.path.exists(dest) and not force:
            click.echo(f"⚠️  Skipped {filename} (exists). Use --force to overwrite.")
        else:
            try:
                shutil.copy2(src, dest)
                click.echo(f"✅ Created {filename}")
            except Exception as e:
                click.echo(f"❌ Failed to copy {filename}: {e}")

    click.echo("\n✨ LoFi Gate initialized! Tell your Agent to check .agent/skills/lofi-gate/SKILL.md")

@cli.command()
@click.option('--parallel', is_flag=True, help="Run checks in parallel.")
def verify(parallel):
    """Run the verification suite (Tests, Lint, Security)."""
    # Simply delegate to the logic engine
    sys.exit(run_checks(parallel=parallel))

if __name__ == "__main__":
    cli()
