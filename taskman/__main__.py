
import typer
from datetime import datetime
import uuid

app = typer.Typer()

tasks_db = []

@app.command()
def add(title: str, description: str = '', priority: str = 'medium'):
    """Add a new task."""
    task_id = str(uuid.uuid4())[:8]
    task = {
        'id': task_id,
        'title': title,
        'description': description,
        'priority': priority,
        'status': 'pending',
        'created': datetime.utcnow().isoformat()
    }
    tasks_db.append(task)
    typer.echo(f'✓ Created task: {task_id}')

@app.command()
def list(all: bool = False, completed: bool = False, pending: bool = False):
    """List tasks."""
    filtered_tasks = [
        task for task in tasks_db
        if all or (completed and task['status'] == 'completed') or (pending and task['status'] == 'pending') or (not completed and not pending and task['status'] == 'pending')
    ]
    typer.echo(f"{'ID':<8} {'Title':<20} {'Priority':<10} {'Status':<10} {'Created'}")
    typer.echo("-" * 60)
    for task in filtered_tasks:
        typer.echo(f"{task['id']:<8} {task['title']:<20} {task['priority']:<10} {task['status']:<10} {task['created']}")

if __name__ == "__main__":
    app()
