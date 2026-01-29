"""Progress indicators for DevOS CLI operations."""

import click
import time
from typing import Iterator, Optional


class ProgressSpinner:
    """Simple spinner for operations without known duration."""
    
    def __init__(self, text: str = "Processing..."):
        self.text = text
        self.spinner_chars = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.delay = 0.1
    
    def __enter__(self):
        self.start_time = time.time()
        self._spinner_thread = click.progressbar(
            length=100,
            label=self.text,
            show_eta=False,
            show_percent=False
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            click.echo(f"✅ {self.text} completed")
        else:
            click.echo(f"❌ {self.text} failed")
    
    def update(self):
        """Update spinner position."""
        pass


class ProgressBar:
    """Progress bar for operations with known steps."""
    
    def __init__(self, steps: int, text: str = "Processing"):
        self.steps = steps
        self.text = text
        self.current = 0
    
    def __enter__(self):
        self.bar = click.progressbar(
            length=self.steps,
            label=self.text,
            show_eta=True,
            show_percent=True
        )
        self.bar.render_progress()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.bar.update(self.steps)
            click.echo(f"\n✅ {self.text} completed")
        else:
            click.echo(f"\n❌ {self.text} failed")
    
    def step(self, message: Optional[str] = None):
        """Advance progress by one step."""
        self.current += 1
        if message:
            self.bar.label = f"{self.text} - {message}"
        self.bar.update(1)
        time.sleep(0.1)  # Brief pause for visual feedback


def show_operation_status(operation: str, success: bool, details: Optional[str] = None):
    """Show operation status with emoji and details."""
    
    if success:
        click.echo(f"✅ {operation}")
        if details:
            click.echo(f"   {details}")
    else:
        click.echo(f"❌ {operation}")
        if details:
            click.echo(f"   {details}")


def show_info(message: str, details: Optional[str] = None):
    """Show informational message."""
    click.echo(f"ℹ️  {message}")
    if details:
        click.echo(f"   {details}")


def show_warning(message: str, details: Optional[str] = None):
    """Show warning message."""
    click.echo(f"⚠️  {message}")
    if details:
        click.echo(f"   {details}")


def show_success(message: str, details: Optional[str] = None):
    """Show success message."""
    click.echo(f"✅ {message}")
    if details:
        click.echo(f"   {details}")
