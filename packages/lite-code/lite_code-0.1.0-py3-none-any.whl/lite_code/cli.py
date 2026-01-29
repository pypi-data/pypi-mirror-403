import os
import logging
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory

from lite_code.config import Config
from lite_code.agent import RefactoringAgent
from lite_code.commands import CommandHandler
from lite_code.tools import generate_diff, write_file
from lite_code.utils import setup_logging, format_diff_for_display, detect_language

logger = logging.getLogger(__name__)


class InteractiveCLI:
    """Interactive CLI for lite-code."""
    
    def __init__(self):
        self.console = Console()
        self.config = Config()
        self.command_handler = CommandHandler()
        self.api_key = None
        self.model = "zai-glm-4.7"
        self.backup_mode = False
        self.agent = None
        self.history_file = Path.home() / ".lite-code" / "history.txt"
    
    def start(self):
        """Start the interactive CLI."""
        setup_logging(logging.INFO)
        
        self.console.print(Panel.fit(
            "[bold cyan]🚀 Welcome to lite-code![/bold cyan]\n"
            "[dim]AI-powered code refactoring assistant[/dim]",
            border_style="cyan"
        ))
        
        self._load_configuration()
        self._setup_agent()
        self._repl_loop()
    
    def _load_configuration(self):
        """Load configuration from file."""
        config_data = self.config.load()
        
        if config_data:
            self.api_key = config_data.get("api_key")
            self.model = config_data.get("model", "zai-glm-4.7")
            self.backup_mode = config_data.get("backup_mode", False)
            self.command_handler.set_context(config_data.get("context", []))
            
            context_count = len(self.command_handler.get_context())
            if context_count > 0:
                self.console.print(f"[green]✓[/green] Loaded context: {context_count} items")
        
        if not self.api_key:
            self._prompt_api_key()
        
        if not self.model:
            self.model = Prompt.ask(
                "[yellow]Enter model name[/yellow]",
                default="zai-glm-4.7"
            )
        
        self._save_configuration()
    
    def _prompt_api_key(self):
        """Prompt user for API key."""
        self.console.print("\n[yellow]No API key found.[/yellow]")
        self.api_key = Prompt.ask(
            "[cyan]Enter your Cerebras API key[/cyan]",
            password=True
        )
        self.console.print("[green]✓[/green] API key saved")
    
    def _setup_agent(self):
        """Setup the refactoring agent."""
        try:
            self.agent = RefactoringAgent(api_key=self.api_key, model=self.model)
        except Exception as e:
            self.console.print(f"[red]✗ Error initializing agent: {e}[/red]")
            raise
    
    def _save_configuration(self):
        """Save current configuration."""
        self.config.save(
            self.api_key,
            self.model,
            self.command_handler.get_context(),
            self.backup_mode
        )
    
    def _repl_loop(self):
        """Main REPL loop."""
        session = PromptSession(
            history=FileHistory(str(self.history_file)) if self.history_file.exists() else None
        )
        
        while True:
            try:
                user_input = session.prompt("lite-code > ")
                
                if not user_input.strip():
                    continue
                
                command, argument, is_command = self.command_handler.parse_command(user_input)
                
                if is_command:
                    self._handle_command(command, argument)
                else:
                    self._handle_task(argument)
            
            except KeyboardInterrupt:
                self.console.print("\n[yellow]Use 'exit' to quit[/yellow]")
            except EOFError:
                self._exit()
                break
    
    def _handle_command(self, command: str, argument: str):
        """Handle special commands."""
        if command == "file":
            success, message = self.command_handler.handle_file_reference(argument)
            if success:
                self.console.print(f"[green]✓[/green] {message}")
            else:
                self.console.print(f"[red]✗[/red] {message}")
        
        elif command == "folder":
            success, message = self.command_handler.handle_folder_reference(argument)
            if success:
                self.console.print(f"[green]✓[/green] {message}")
            else:
                self.console.print(f"[red]✗[/red] {message}")
        
        elif command == "help":
            self.console.print(self.command_handler.show_help())
        
        elif command == "settings":
            self._handle_settings()
        
        elif command == "clear":
            success, message = self.command_handler.clear_context()
            self.console.print(f"[green]✓[/green] {message}")
        
        elif command in ["exit", "quit"]:
            self._exit()
    
    def _handle_settings(self):
        """Handle settings menu."""
        while True:
            self.console.print("\n[bold]Settings:[/bold]")
            self.console.print(f"  1. Change API key")
            self.console.print(f"  2. Change model (current: {self.model})")
            self.console.print(f"  3. Toggle backup mode (current: {'enabled' if self.backup_mode else 'disabled'})")
            self.console.print(f"  4. Back")
            
            choice = Prompt.ask("\nSelect option", choices=["1", "2", "3", "4"])
            
            if choice == "1":
                self.api_key = Prompt.ask("Enter new API key", password=True)
                self.console.print("[green]✓[/green] API key updated")
                self._setup_agent()
            
            elif choice == "2":
                self.model = Prompt.ask("Enter model name", default=self.model)
                self.console.print(f"[green]✓[/green] Model updated to {self.model}")
                self._setup_agent()
            
            elif choice == "3":
                self.backup_mode = not self.backup_mode
                mode = "enabled" if self.backup_mode else "disabled"
                self.console.print(f"[green]✓[/green] Backup mode {mode}")
            
            elif choice == "4":
                break
            
            self._save_configuration()
    
    def _handle_task(self, task: str):
        """Handle refactoring task."""
        context = self.command_handler.get_context()
        
        if not context:
            self.console.print("[yellow]⚠ No context set. Use @filename or /folder to add files.[/yellow]")
            return
        
        self.console.print(f"\n[green]✓[/green] Analyzing {len(context)} file(s)...")
        
        with self.console.status("[bold green]AI is analyzing your code...[/bold green]"):
            result = self.agent.refactor(task, context)
        
        if result["status"] == "error":
            self.console.print(f"\n[red]✗ Error: {result['error']}[/red]")
            return
        
        if result["status"] == "incomplete":
            self.console.print(f"\n[yellow]⚠ Refactoring incomplete: {result['reasoning']}[/yellow]")
            return
        
        self.console.print(f"\n[green]✓[/green] Refactoring complete!")
        self.console.print(f"[dim]Reasoning: {result['reasoning']}[/dim]")
        
        changes = result.get("changes", {})
        
        if not changes:
            self.console.print("[yellow]No changes were made.[/yellow]")
            return
        
        self._process_changes(changes)
    
    def _process_changes(self, changes: dict):
        """Process changes with interactive approval."""
        self.console.print(f"\n[bold]Files to be modified: {len(changes)}[/bold]\n")
        
        approved_count = 0
        skipped_count = 0
        
        for idx, (file_path, new_content) in enumerate(changes.items(), 1):
            self.console.print(f"[bold cyan]File {idx}/{len(changes)}: {file_path}[/bold cyan]")
            
            try:
                original_path = Path(file_path)
                if not original_path.exists():
                    self.console.print(f"[yellow]⚠ File not found: {file_path}[/yellow]")
                    continue
                
                original_content = original_path.read_text(encoding='utf-8')
                diff_result = generate_diff(original_content, new_content)
                
                if "diff" in diff_result and diff_result["diff"]:
                    self.console.print(Panel(
                        format_diff_for_display(diff_result["diff"], file_path),
                        border_style="dim",
                        padding=(0, 1)
                    ))
                    
                    approved = Confirm.ask("Apply changes?", default=False)
                    
                    if approved:
                        if self.backup_mode:
                            self._apply_with_backup(file_path, new_content)
                        else:
                            self._apply_in_place(file_path, new_content)
                        approved_count += 1
                    else:
                        skipped_count += 1
                        self.console.print("[yellow]Skipped[/yellow]\n")
                else:
                    self.console.print("[yellow]No changes to show[/yellow]\n")
            
            except Exception as e:
                self.console.print(f"[red]✗ Error processing {file_path}: {e}[/red]\n")
        
        self.console.print(f"\n[bold]Summary:[/bold]")
        self.console.print(f"  • Applied: {approved_count} file(s)")
        self.console.print(f"  • Skipped: {skipped_count} file(s)")
    
    def _apply_in_place(self, file_path: str, content: str):
        """Apply changes in-place."""
        try:
            result = write_file(file_path, content)
            if "error" in result:
                self.console.print(f"[red]✗ Error: {result['error']}[/red]")
            else:
                self.console.print("[green]✓ Applied changes[/green]\n")
        except Exception as e:
            self.console.print(f"[red]✗ Error: {e}[/red]\n")
    
    def _apply_with_backup(self, file_path: str, content: str):
        """Apply changes with backup."""
        try:
            from lite_code.utils import create_backup_folder, copy_to_backup
            
            original_path = Path(file_path)
            backup_path = create_backup_folder(str(original_path.parent))
            copy_to_backup(str(original_path), backup_path)
            
            result = write_file(file_path, content)
            if "error" in result:
                self.console.print(f"[red]✗ Error: {result['error']}[/red]")
            else:
                self.console.print(f"[green]✓ Applied changes (backup: {backup_path})[/green]\n")
        except Exception as e:
            self.console.print(f"[red]✗ Error: {e}[/red]\n")
    
    def _exit(self):
        """Exit the CLI."""
        self._save_configuration()
        self.console.print("\n[green]✓[/green] Configuration saved")
        self.console.print("[dim]Goodbye! 👋[/dim]")
