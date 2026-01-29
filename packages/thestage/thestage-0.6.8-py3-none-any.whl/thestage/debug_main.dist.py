from thestage import __app_name__
from thestage.controllers.base_controller import app as main_app

from thestage.docker_container.communication.docker_command import app as container_app
from thestage.instance.communication.instance_command import app as instance_app
from thestage.project.communication.project_command import app as project_app
from thestage.config.communication.config_command import app as config_app
from thestage.task.communication.task_command import app as task_app

main_app.add_typer(container_app, name="container")
main_app.add_typer(instance_app, name="instance")
main_app.add_typer(config_app, name="config")
main_app.add_typer(project_app, name="project")
main_app.add_typer(task_app, name="task")

def main():
    project_app([
        "run",
        "-wd",
        "/Users/alexey/Documents/clonetest",
        "-cid",
        '62-1',
        '-t',
        'task',
        "echo 123",
        "-nl"
    ], prog_name=__app_name__)

if __name__ == "__main__":
    main()