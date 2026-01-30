from textual.app import App, ComposeResult
from textual.widgets import (
    Header,
    Footer,
    ListView,
    ListItem,
    Input,
    Static,
)
from textual.reactive import reactive
from textual.message import Message
from textual import events
from todox.store import load
import time


# ---------- Custom Todo Item ----------
class TodoItem(ListItem):
    selected = reactive(False)

    def __init__(self, todo: dict):
        super().__init__()
        self.todo = todo
        self.start_time = None

    def compose(self) -> ComposeResult:
        status = "✅" if self.todo["done"] else "⬜"
        tags = " ".join(f"#{t}" for t in self.todo.get("tags", []))
        timer = "⏱ " if self.start_time else ""
        
        prio = self.todo.get("priority", "medium")
        prio_color = "red" if prio == "high" else "yellow" if prio == "medium" else "green"
        prio_icon = "!!!" if prio == "high" else "!!" if prio == "medium" else "!"
        
        due = f"📅 {self.todo['due_date']}" if self.todo.get("due_date") else ""
        
        markup_open = "[strike]" if self.todo["done"] else ""
        markup_close = "[/strike]" if self.todo["done"] else ""

        yield Static(
            f"{markup_open}"
            f"{status} "
            f"[{prio_color}]{prio_icon}[/{prio_color}] "
            f"{self.todo['title']} "
            f"{markup_close} "
            f"[blue]{tags}[/blue] "
            f"[magenta]{due}[/magenta] "
            f"{timer}"
        )

    def toggle_done(self):
        self.todo["done"] = not self.todo["done"]
        self.refresh()

    def toggle_select(self):
        self.selected = not self.selected
        self.styles.background = "darkblue" if self.selected else None

    def start_timer(self):
        self.start_time = time.time()
        self.refresh()

    def stop_timer(self):
        self.start_time = None
        self.refresh()

    def cycle_priority(self):
        prio_order = ["low", "medium", "high"]
        current = self.todo.get("priority", "medium")
        try:
            next_idx = (prio_order.index(current) + 1) % 3
        except ValueError:
            next_idx = 1
        self.todo["priority"] = prio_order[next_idx]
        self.refresh()


# ---------- Main App ----------
class TodoApp(App):
    CSS = """
    Input {
        dock: top;
        margin: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("x", "toggle_done", "Toggle done"),
        ("space", "select", "Select"),
        ("t", "toggle_timer", "Time track"),
        ("p", "priority", "Priority"),
        ("s", "sort", "Sort (Prio)"),
    ]

    # source of truth
    all_todos = reactive(list)

    # UI only
    search_query = reactive("")
    sort_by_prio = reactive(False)

    def compose(self) -> ComposeResult:
        yield Header()
        yield Input(placeholder="🔍 Search todos...", id="search")
        self.list_view = ListView()
        yield self.list_view
        yield Footer()

    def on_mount(self):
        data = load()
        self.all_todos = data["todos"]
        self.refresh_list()

    # ---------- Rendering ----------
    def refresh_list(self):
        self.list_view.clear()

        if self.sort_by_prio:
            # Sort by priority (high > medium > low)
            prio_map = {"high": 0, "medium": 1, "low": 2}
            sorted_todos = sorted(
                self.filtered_todos, 
                key=lambda t: prio_map.get(t.get("priority", "medium"), 1)
            )
        else:
            sorted_todos = self.filtered_todos

        for todo in sorted_todos:
            self.list_view.append(TodoItem(todo))

    @property
    def filtered_todos(self):
        if not self.search_query:
            return self.all_todos

        q = self.search_query.lower()
        return [
            t for t in self.all_todos
            if q in t["title"].lower()
            or any(q in tag.lower() for tag in t.get("tags", []))
        ]

    # ---------- Events ----------
    def on_input_changed(self, event: Input.Changed):
        self.search_query = event.value
        self.refresh_list()

    def action_select(self):
        item = self.list_view.highlighted_child
        if isinstance(item, TodoItem):
            item.toggle_select()

    def action_toggle_timer(self):
        item = self.list_view.highlighted_child
        if isinstance(item, TodoItem):
            if item.start_time:
                item.stop_timer()
            else:
                item.start_timer()

    def action_priority(self):
        item = self.list_view.highlighted_child
        if isinstance(item, TodoItem):
            item.cycle_priority()
            from todox.store import save
            save({"todos": self.all_todos, "last_active": None})

    def action_sort(self):
        self.sort_by_prio = not self.sort_by_prio
        self.refresh_list()
        
    def action_toggle_done(self):
        item = self.list_view.highlighted_child
        if isinstance(item, TodoItem):
            item.toggle_done()
            from todox.store import save
            save({"todos": self.all_todos, "last_active": None})
            self.refresh_list()


if __name__ == "__main__":
    TodoApp().run()
