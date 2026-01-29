"""
Rich Progress Indicators - Enhanced User Experience
Provides beautiful, informative progress indicators for DevOS operations.
"""

import time
import threading
from typing import Iterator, Optional, Dict, Any, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
import click


@dataclass
class ProgressMetrics:
    """Metrics for progress tracking."""
    total: int
    completed: int
    current_item: str
    start_time: datetime
    estimated_completion: Optional[datetime] = None
    rate: Optional[float] = None  # items per second


class RichProgressBar:
    """Enhanced progress bar with metrics and status."""
    
    def __init__(self, total: int, description: str = "Processing", show_eta: bool = True, show_rate: bool = True):
        self.total = total
        self.description = description
        self.show_eta = show_eta
        self.show_rate = show_rate
        self.completed = 0
        self.start_time = time.time()
        self.last_update = self.start_time
        self.current_item = ""
        
    def update(self, advance: int = 1, current_item: str = ""):
        """Update progress."""
        self.completed += advance
        self.current_item = current_item
        self.last_update = time.time()
        
    def get_metrics(self) -> ProgressMetrics:
        """Calculate current metrics."""
        elapsed = time.time() - self.start_time
        rate = self.completed / elapsed if elapsed > 0 else 0
        
        # Estimate completion time
        if rate > 0 and self.completed < self.total:
            remaining = (self.total - self.completed) / rate
            estimated_completion = datetime.now() + timedelta(seconds=remaining)
        else:
            estimated_completion = None
            
        return ProgressMetrics(
            total=self.total,
            completed=self.completed,
            current_item=self.current_item,
            start_time=datetime.fromtimestamp(self.start_time),
            estimated_completion=estimated_completion,
            rate=rate
        )
    
    def render(self) -> str:
        """Render progress bar."""
        metrics = self.get_metrics()
        percentage = (metrics.completed / metrics.total) * 100 if metrics.total > 0 else 0
        
        # Progress bar
        bar_width = 30
        filled = int(bar_width * percentage / 100)
        bar = "█" * filled + "░" * (bar_width - filled)
        
        # Main progress line
        progress_line = f"{self.description}: [{bar}] {percentage:.1f}% ({metrics.completed}/{metrics.total})"
        
        # Additional info
        info_lines = []
        
        if self.current_item:
            info_lines.append(f"📁 {self.current_item}")
        
        if self.show_rate and metrics.rate:
            info_lines.append(f"⚡ {metrics.rate:.1f} items/sec")
        
        if self.show_eta and metrics.estimated_completion:
            eta = metrics.estimated_completion.strftime("%H:%M:%S")
            info_lines.append(f"⏰ ETA: {eta}")
        
        # Combine lines
        if info_lines:
            return f"{progress_line}\n   {' '.join(info_lines)}"
        else:
            return progress_line
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is None:
            # Success
            metrics = self.get_metrics()
            elapsed = time.time() - self.start_time
            click.echo(f"\n✅ {self.description} completed in {elapsed:.1f}s")
        else:
            # Error
            click.echo(f"\n❌ {self.description} failed")


class MultiProgressManager:
    """Manage multiple concurrent progress bars."""
    
    def __init__(self):
        self.bars: Dict[str, RichProgressBar] = {}
        self.active_bar: Optional[str] = None
        self.render_thread: Optional[threading.Thread] = None
        self.running = False
        
    def add_bar(self, name: str, total: int, description: str) -> RichProgressBar:
        """Add a new progress bar."""
        bar = RichProgressBar(total, description)
        self.bars[name] = bar
        return bar
    
    def set_active(self, name: str):
        """Set the active progress bar."""
        self.active_bar = name
    
    def update(self, name: str, advance: int = 1, current_item: str = ""):
        """Update a specific progress bar."""
        if name in self.bars:
            self.bars[name].update(advance, current_item)
    
    def render_all(self) -> str:
        """Render all progress bars."""
        lines = []
        for name, bar in self.bars.items():
            prefix = "👉 " if name == self.active_bar else "   "
            lines.append(f"{prefix}{bar.render()}")
        return "\n".join(lines)
    
    def start_rendering(self):
        """Start background rendering."""
        self.running = True
        self.render_thread = threading.Thread(target=self._render_loop, daemon=True)
        self.render_thread.start()
    
    def stop_rendering(self):
        """Stop background rendering."""
        self.running = False
        if self.render_thread:
            self.render_thread.join(timeout=1)
    
    def _render_loop(self):
        """Background rendering loop."""
        while self.running:
            # Clear screen and render
            click.clear()
            click.echo(self.render_all())
            time.sleep(0.1)


class AnimatedSpinner:
    """Animated spinner with status messages."""
    
    def __init__(self, description: str = "Working", frames: Optional[list] = None):
        self.description = description
        self.frames = frames or ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.current_frame = 0
        self.running = False
        self.thread: Optional[threading.Thread] = None
        
    def start(self):
        """Start the spinner."""
        self.running = True
        self.thread = threading.Thread(target=self._spin, daemon=True)
        self.thread.start()
        
    def stop(self, message: str = "Done"):
        """Stop the spinner."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=0.2)
        click.echo(f"\r✅ {message}")
        
    def _spin(self):
        """Spinner animation loop."""
        while self.running:
            frame = self.frames[self.current_frame]
            click.echo(f"\r{frame} {self.description}...", nl=False)
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            time.sleep(0.1)
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is None:
            self.stop(self.description)
        else:
            self.stop(f"Failed: {self.description}")


class StepProgress:
    """Step-by-step progress indicator."""
    
    def __init__(self, steps: list, description: str = "Process"):
        self.steps = steps
        self.description = description
        self.current_step = 0
        self.step_start_time = None
        
    def start_step(self, step_name: str):
        """Start a new step."""
        if self.step_start_time:
            elapsed = time.time() - self.step_start_time
            click.echo(f"   ✅ Completed in {elapsed:.1f}s")
        
        self.current_step += 1
        self.step_start_time = time.time()
        
        total_steps = len(self.steps)
        click.echo(f"\n📍 Step {self.current_step}/{total_steps}: {step_name}")
        click.echo("   " + "─" * 40)
        
    def complete(self):
        """Complete all steps."""
        if self.step_start_time:
            elapsed = time.time() - self.step_start_time
            click.echo(f"   ✅ Completed in {elapsed:.1f}s")
        
        click.echo(f"\n🎉 {self.description} completed!")
        
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is None:
            self.complete()


# Convenience functions
def show_progress(total: int, description: str = "Processing") -> RichProgressBar:
    """Show a rich progress bar."""
    return RichProgressBar(total, description)


def show_spinner(description: str = "Working") -> AnimatedSpinner:
    """Show an animated spinner."""
    return AnimatedSpinner(description)


def show_steps(steps: list, description: str = "Process") -> StepProgress:
    """Show step-by-step progress."""
    return StepProgress(steps, description)


def show_operation_with_progress(operation: Callable, total: int, description: str):
    """Show progress while executing an operation."""
    with show_progress(total, description) as bar:
        for i in range(total):
            result = operation(i)
            bar.update(1, f"Item {i+1}")
            yield result
