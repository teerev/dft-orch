import json
import os
from taskman.models import Task

class TaskStorage:
    TASKS_FILE = os.path.expanduser("~/.taskman/tasks.json")

    def __init__(self):
        self.tasks = []
        self.load()

    def add(self, task: Task):
        self.tasks.append(task)
        self.save()

    def get(self, task_id: str):
        return next((task for task in self.tasks if task.id == task_id), None)

    def list_all(self):
        return self.tasks

    def update(self, task: Task):
        for i, t in enumerate(self.tasks):
            if t.id == task.id:
                self.tasks[i] = task
                self.save()
                break

    def delete(self, task_id: str):
        self.tasks = [task for task in self.tasks if task.id != task_id]
        self.save()

    def save(self):
        os.makedirs(os.path.dirname(self.TASKS_FILE), exist_ok=True)
        with open(self.TASKS_FILE, 'w') as f:
            json.dump([task.__dict__ for task in self.tasks], f, default=str)

    def load(self):
        if os.path.exists(self.TASKS_FILE):
            with open(self.TASKS_FILE, 'r') as f:
                tasks_data = json.load(f)
                self.tasks = [Task(**task) for task in tasks_data]
        else:
            self.tasks = []
