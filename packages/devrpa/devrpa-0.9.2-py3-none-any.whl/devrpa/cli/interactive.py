from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, ListView, ListItem, Label, Input, TabbedContent, TabPane, TextArea
from textual.reactive import reactive
import json

from rich.text import Text

class StepItem(ListItem):
    """A detailed list item representing a workflow step."""
    def __init__(self, step_name: str, step_type: str) -> None:
        super().__init__()
        self.step_name = step_name
        self.step_type = step_type
        self.config = {}
        # Status tracking
        self.success = False
        self.failed = False
        self.duration = None
        self.description = ""

    def render(self) -> Text:
        # Label based on type
        type_labels = {
            "API": "[API]",
            "Database": "[DB]",
            "Transform": "[TF]",
        }
        label = type_labels.get(self.step_type, "[STEP]")
        
        # Status indicator
        status = "[DONE]" if self.success else "[FAIL]" if self.failed else "[WAIT]"
        status_color = "green" if self.success else "red" if self.failed else "dim"
        
        # Duration
        duration = f"{self.duration:.1f}s" if self.duration is not None else ""
        
        text = Text()
        text.append(f"{label} ", style="bold")
        text.append(f"{self.step_name}", style="cyan")
        text.append(f" {duration} ", style="dim")
        text.append(status, style=status_color)
        
        # Brief description/summary
        if self.step_type == "API" and "url" in self.config:
             text.append(f"\n    {self.config['url']}", style="dim")
        elif self.step_type == "Database" and "query" in self.config:
             # Truncate query
             query = self.config['query']
             if len(query) > 30: query = query[:27] + "..."
             text.append(f"\n    {query}", style="dim")
            
        return text

class WorkflowPersistence:
    @staticmethod
    def save(steps: list, filename: str) -> None:
        """Save steps configuration to JSON."""
        data = []
        for step in steps:
            data.append({
                "name": step.step_name,
                "type": step.step_type,
                "config": step.config
            })
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def load(filename: str) -> list[dict]:
        """Load steps configuration from JSON."""
        with open(filename, "r") as f:
            return json.load(f)

class Sidebar(Container):
    """Sidebar with step list and add buttons."""
    
    def compose(self) -> ComposeResult:
        yield Label("Workflow Steps", classes="header")
        yield ListView(id="step-list")
        yield Label("Add Step", classes="header")
        with Vertical(id="add-buttons"):
            yield Button("API Request", id="add-api", variant="primary")
            yield Button("Database", id="add-db")
            yield Button("Transform", id="add-transform")
            
        yield Label("Management", classes="header")
        with Vertical(id="manage-buttons"):
            yield Button("Save JSON", id="save-json")
            yield Button("Load JSON", id="load-json")


from textual.widgets import Select

class StepConfigPanel(Container):
    """Configuration form for the selected step."""
    
    current_step = reactive(None)

    def compose(self) -> ComposeResult:
        yield Label("Step Configuration", classes="header")
        yield Container(id="config-form")

    def watch_current_step(self, step) -> None:
        """Update the form when the step changes."""
        form = self.query_one("#config-form")
        form.remove_children()
        
        if step:
            # Header with type info
            form.mount(Label(f"Step Type: {step.step_type}", classes="step-type-label"))
            
            # Common Name field
            form.mount(Label("Step Name:"))
            name_input = Input(value=step.step_name, id="step-name", placeholder="Enter step name")
            form.mount(name_input)
            
            # Dynamic fields based on type
            # Dynamic fields based on type
            if step.step_type == "API":
                form.mount(Label("URL:"))
                url_input = Input(value=step.config.get("url", ""), placeholder="https://api.example.com/users", id="api-url")
                form.mount(url_input)
                
                form.mount(Label("Method:"))
                method_select = Select(
                    [(m, m) for m in ["GET", "POST", "PUT", "DELETE", "PATCH"]],
                    value=step.config.get("method", "GET"),
                    id="api-method",
                    allow_blank=False
                )
                form.mount(method_select)
                
                form.mount(Label("Headers (JSON):"))
                headers_val = step.config.get("headers", '{\n  "Content-Type": "application/json"\n}')
                headers_input = TextArea(headers_val, language="json", id="api-headers")
                form.mount(headers_input)

                form.mount(Label("Output Variable:"))
                output_input = Input(value=step.config.get("output", ""), placeholder="response_data", id="step-output")
                form.mount(output_input)

                # Advanced Options
                form.mount(Label("Advanced Options", classes="header"))
                
                from textual.widgets import Checkbox
                form.mount(Checkbox("Enable Retry", value=step.config.get("retry", False), id="api-retry"))
                form.mount(Checkbox("Cache Response", value=step.config.get("cache", False), id="api-cache"))
                
                form.mount(Label("Timeout (seconds):"))
                timeout_input = Input(value=str(step.config.get("timeout", "30")), placeholder="30", id="api-timeout")
                form.mount(timeout_input)

            elif step.step_type == "Database":
                form.mount(Label("Connection String:"))
                conn_input = Input(value=step.config.get("connection", ""), placeholder="postgresql://user:pass@localhost/db", id="db-connection")
                form.mount(conn_input)
                
                form.mount(Label("SQL Query:"))
                query_val = step.config.get("query", "SELECT * FROM users LIMIT 10")
                query_input = TextArea(query_val, language="sql", id="db-query")
                form.mount(query_input)

                form.mount(Label("Output Variable:"))
                output_input = Input(value=step.config.get("output", ""), placeholder="db_results", id="step-output")
                form.mount(output_input)
                
            elif step.step_type == "Transform":
                form.mount(Label("Transform Function (Python):"))
                code_val = step.config.get("code", "def transform(data):\n    return data")
                code_input = TextArea(code_val, language="python", id="transform-code")
                form.mount(code_input)

                form.mount(Label("Output Variable:"))
                output_input = Input(value=step.config.get("output", ""), placeholder="transform_result", id="step-output")
                form.mount(output_input)
                
            # Action Buttons
            form.mount(
                Horizontal(
                    Button("Test Step", id="test-step", variant="primary"),
                    Button("↑ Up", id="move-up"),
                    Button("↓ Down", id="move-down"),
                    Button("Delete", id="delete-step", variant="error"),
                    classes="button-row"
                )
            )
        else:
            form.mount(Label("Select a step to configure", classes="placeholder-text"))
            
    def on_input_changed(self, event: Input.Changed) -> None:
        """Update config when inputs change."""
        if not self.current_step: return
        
        if event.input.id == "step-name":
            self.current_step.step_name = event.value
        elif event.input.id == "api-url":
            self.current_step.config["url"] = event.value
        elif event.input.id == "db-connection":
            self.current_step.config["connection"] = event.value
        elif event.input.id == "step-output":
            self.current_step.config["output"] = event.value
        elif event.input.id == "api-timeout":
            self.current_step.config["timeout"] = event.value
            
        self.current_step.refresh()
            
    def on_select_changed(self, event: Select.Changed) -> None:
        if not self.current_step: return
        if event.select.id == "api-method":
            self.current_step.config["method"] = event.value
        self.current_step.refresh()

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        if not self.current_step: return
        if event.text_area.id == "api-headers":
            self.current_step.config["headers"] = event.text_area.text
        elif event.text_area.id == "db-query":
            self.current_step.config["query"] = event.text_area.text
        elif event.text_area.id == "transform-code":
            self.current_step.config["code"] = event.text_area.text
        self.current_step.refresh()

    def on_checkbox_changed(self, event) -> None:
        """Handle checkbox changes."""
        if not self.current_step: return
        if event.checkbox.id == "api-retry":
            self.current_step.config["retry"] = event.value
        elif event.checkbox.id == "api-cache":
            self.current_step.config["cache"] = event.value
        self.current_step.refresh()

from textual.widgets import RichLog
import subprocess
import sys

import re

class WorkflowValidator:
    @staticmethod
    def validate(steps: list) -> list[str]:
        """Validate workflow configuration, return list of errors."""
        errors = []
        if not steps:
            errors.append("Workflow has no steps.")
            return errors
            
        available_vars = set()
        
        for i, step in enumerate(steps):
            step_name = step.step_name or f"step_{i+1}"
            
            # Check required fields
            if step.step_type == "API":
                url = step.config.get("url", "")
                if not url:
                    errors.append(f"Step '{step_name}': Missing URL")
                
                # Check variable usage in URL
                vars_in_url = re.findall(r'\{([^}]+)\}', url)
                for var in vars_in_url:
                    if var.startswith("secrets:"): continue # Skip secrets
                    if var not in available_vars:
                         errors.append(f"Step '{step_name}': Reference to undefined variable '{var}'")

            elif step.step_type == "Database":
                if not step.config.get("connection"):
                    errors.append(f"Step '{step_name}': Missing connection string")
                if not step.config.get("query"):
                    errors.append(f"Step '{step_name}': Missing SQL query")

            # Track output variable
            output_var = step.config.get("output")
            if output_var:
                available_vars.add(output_var)
                
        return errors

class CodePreview(Container):
    """Displays the generated code and allows execution."""
    
    def compose(self) -> ComposeResult:
        yield Label("Generated Code", classes="header")
        yield TextArea(language="python", id="code-output", read_only=True)
        yield Horizontal(
            Button("Save to 'my_workflow.py'", id="save-workflow"),
            Button("Run Workflow", id="run-workflow", variant="success"),
            classes="button-row"
        )
        yield Label("Execution Output", classes="header")
        yield RichLog(id="execution-log", markup=True)

    def on_mount(self):
        self.steps = []

    def update_code(self, steps):
        self.steps = steps # Store for validation/execution
        code = "from devrpa import flow\n\n"
        code += 'workflow = (flow("my_workflow")'
        
        for step in steps:
            if step.step_type == "API":
                url = step.config.get("url", "https://api.example.com")
                code += f'\n    .from_api("{url}")'
            elif step.step_type == "Database":
                query = step.config.get("query", "SELECT 1")
                code += f'\n    .from_db("{query}")'
            elif step.step_type == "Transform":
                 code += f'\n    .transform(lambda x: x)'
        
        code += "\n)"
                 
        textarea = self.query_one("#code-output", TextArea)
        textarea.text = code

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle save and run actions."""
        if event.button.id == "save-workflow":
             self.save_workflow()
        elif event.button.id == "run-workflow":
             # Validate first
             errors = WorkflowValidator.validate(self.steps)
             log = self.query_one("#execution-log", RichLog)
             log.clear()
             
             if errors:
                 log.write("[red]Validation Failed:[/red]")
                 for err in errors:
                     log.write(f"[red]- {err}[/red]")
                 return

             self.run_workflow()

    def save_workflow(self) -> str:
        textarea = self.query_one("#code-output", TextArea)
        filename = "my_workflow.py"
        with open(filename, "w") as f:
            f.write(textarea.text)
        log = self.query_one("#execution-log", RichLog)
        log.write(f"[green]Saved to {filename}[/]")
        return filename

    def run_workflow(self):
        filename = self.save_workflow()
        log = self.query_one("#execution-log", RichLog)
        log.write(f"[yellow]Running {filename}...[/]")
        
        try:
            # Run in a subprocess to capture output
            result = subprocess.run(
                [sys.executable, filename], # Using sys.executable to ensure we use the same python
                capture_output=True,
                text=True
            )
            if result.stdout:
                log.write(result.stdout)
            if result.stderr:
                log.write(f"[red]{result.stderr}[/]")
            
            if result.returncode == 0:
                 log.write("[green]Wrapper completed successfully.[/]")
            else:
                 log.write(f"[red]Workflow failed with code {result.returncode}[/]")
                 
        except Exception as e:
            log.write(f"[red]Error running workflow: {e}[/]")

class WorkflowBuilderApp(App):
    """A Textual app to build devrpa workflows interactively."""

    CSS = """
    Screen {
        layout: grid;
        grid-size: 2;
        grid-columns: 1fr 3fr;
    }
    
    Sidebar {
        background: $surface;
        border-right: heavy $background;
        height: 100%;
        padding: 1;
    }
    
    StepConfig {
        padding: 2;
        height: 100%;
    }

    .header {
        text-align: center;
        text-style: bold;
        padding-bottom: 1;
    }
    
    #add-buttons Button {
        width: 100%;
        margin-bottom: 1;
    }
    
    ListView {
        height: 50%;
        border: solid $accent;
        margin-bottom: 1;
    }
    
    Input {
        margin-bottom: 1;
    }
    
    .button-row {
        height: 3;
        margin-top: 1;
        margin-bottom: 1;
    }
    
    #execution-log {
        border: solid $accent;
        height: 1fr;
        background: $surface;
    }
    """

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit")
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Sidebar()
        with TabbedContent():
            with TabPane("Configuration"):
                yield StepConfigPanel()
            with TabPane("Code Preview"):
                yield CodePreview()
        yield Footer()



    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        step_list = self.query_one("#step-list", ListView)
        
        # Test Step Logic
        if event.button.id == "test-step":
            config_panel = self.query_one(StepConfigPanel)
            if config_panel.current_step:
                step = config_panel.current_step
                
                # Validation
                error = self.validate_step(step)
                if error:
                    self.notify(error, title="Validation Error", severity="error")
                    return
                
                # Real execution logic
                self.notify(f"Testing step '{step.step_name}'...", title="Testing", severity="information")
                
                try:
                    if step.step_type == "API":
                        import httpx
                        client = httpx.Client()
                        method = step.config.get("method", "GET")
                        url = step.config.get("url", "")
                        headers = json.loads(step.config.get("headers", "{}"))
                        
                        response = client.request(method, url, headers=headers, timeout=float(step.config.get("timeout", 30.0)))
                        step.success = 200 <= response.status_code < 300
                        step.failed = not step.success
                        step.description = f"Status: {response.status_code}"
                        
                    elif step.step_type == "Database":
                        from sqlalchemy import create_engine, text
                        conn_str = step.config.get("connection", "")
                        query = step.config.get("query", "")
                        
                        engine = create_engine(conn_str)
                        with engine.connect() as conn:
                            result = conn.execute(text(query))
                            # Try to fetch some results if it's a SELECT
                            if query.strip().upper().startswith("SELECT"):
                                rows = result.fetchmany(5)
                                step.description = f"Rows fetched: {len(rows)}"
                            else:
                                step.description = "Query executed"
                        step.success = True
                        step.failed = False
                        
                    elif step.step_type == "Transform":
                        code = step.config.get("code", "")
                        # Simple safety check/mock input execution
                        exec_globals = {}
                        exec(code, exec_globals)
                        if "transform" in exec_globals:
                            # Test with sample data
                            sample_input = [{"id": 1, "test": "data"}]
                            result = exec_globals["transform"](sample_input)
                            step.description = f"Output type: {type(result).__name__}"
                            step.success = True
                            step.failed = False
                        else:
                            raise ValueError("Function 'transform' not defined in code.")
                            
                    self.notify(f"Step '{step.step_name}' passed!", title="Test Result", severity="information")
                    
                except Exception as e:
                    step.success = False
                    step.failed = True
                    step.description = str(e)
                    self.notify(f"Step '{step.step_name}' failed: {e}", title="Test Result", severity="error")
                
                step.duration = 0.5 # Placeholder or measure actual time
                step.refresh()
            return
            
        # Delete Step Logic
        if event.button.id == "delete-step":
             config_panel = self.query_one(StepConfigPanel)
             if config_panel.current_step:
                 step_list.remove_children([config_panel.current_step]) # Remove from list
                 config_panel.current_step = None # Clear config
                 self.notify("Step deleted")
             return

        if event.button.id in ("move-up", "move-down"):
            config_panel = self.query_one(StepConfigPanel)
            current_step = config_panel.current_step
            if not current_step: return

            steps = [c for c in step_list.children if isinstance(c, StepItem)]
            try:
                idx = steps.index(current_step)
            except ValueError:
                return

            new_idx = idx
            if event.button.id == "move-up" and idx > 0:
                new_idx = idx - 1
            elif event.button.id == "move-down" and idx < len(steps) - 1:
                new_idx = idx + 1
            
            if new_idx != idx:
                # Swap logic: Re-mount all steps in new order
                # This is a bit heavy but safe for Textual lists
                steps[idx], steps[new_idx] = steps[new_idx], steps[idx]
                
                step_list.remove_children()
                step_list.mount_all(steps)
                
                # Re-select the moved step to keep focus/config
                # We need to wait for mount? Usually mount_all is scheduled. 
                # Selection might be lost, let's try to restore config panel at least.
                config_panel.current_step = current_step
                
            return

        # Persistence Logic
        if event.button.id == "save-json":
            steps = [c for c in step_list.children if isinstance(c, StepItem)]
            try:
                WorkflowPersistence.save(steps, "workflow.json")
                self.notify("Saved to workflow.json")
            except Exception as e:
                self.notify(f"Save failed: {e}", severity="error")
            return

        if event.button.id == "load-json":
            try:
                data = WorkflowPersistence.load("workflow.json")
                step_list.remove_children()
                for item in data:
                    step = StepItem(item["name"], item["type"])
                    step.config = item["config"]
                    step_list.mount(step)
                self.notify("Loaded workflow.json")
            except FileNotFoundError:
                self.notify("workflow.json not found", severity="warning")
            except Exception as e:
                self.notify(f"Load failed: {e}", severity="error")
            return

        step_type = "Unknown"
        if event.button.id == "add-api":
            step_type = "API"
        elif event.button.id == "add-db":
            step_type = "Database"
        elif event.button.id == "add-transform":
            step_type = "Transform"
            
        if step_type != "Unknown":
            count = len(step_list.children) + 1
            new_step = StepItem(f"step_{count}", step_type)
            step_list.mount(new_step)
            
    def validate_step(self, step: StepItem) -> str | None:
        """Validate a single step configuration."""
        if step.step_type == "API":
            if not step.config.get("url"):
                return "API Step requires a URL."
        elif step.step_type == "Database":
            if not step.config.get("connection"):
                return "Database Step requires a Connection String."
            if not step.config.get("query"):
                return "Database Step requires a SQL Query."
        return None

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        """Refresh code when switching to preview tab."""
        if str(event.tab.label) == "Code Preview":
             step_list = self.query_one("#step-list", ListView)
             steps = [child for child in step_list.children if isinstance(child, StepItem)]
             
             # Validate all steps
             errors = []
             for step in steps:
                 err = self.validate_step(step)
                 if err:
                     errors.append(f"{step.step_name}: {err}")
             
             if errors:
                 self.notify("\n".join(errors), title="Validation Errors", severity="warning", timeout=5)
                 
             self.query_one(CodePreview).update_code(steps)



    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle list item selection."""
        step_item = event.item
        if isinstance(step_item, StepItem):
            self.query_one(StepConfigPanel).current_step = step_item

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = "textual-light" if self.theme == "textual-dark" else "textual-dark"

def run_interactive_builder():
    app = WorkflowBuilderApp()
    app.run()
