from typing import Annotated

import typer
from questionary import Choice
from typer import Argument

from spiral.api.types import OrgId, ProjectId
from spiral.cli import ERR_CONSOLE, state
from spiral.cli.chooser import choose


def ask_project(title="Select a project"):
    projects = list(state.spiral.api.projects.list())

    if not projects:
        ERR_CONSOLE.print("No projects found")
        raise typer.Exit(1)

    return choose(
        title,
        [
            Choice(title=f"{project.id} - {project.name}" if project.name else project.id, value=project.id)
            for project in projects
        ],
    )


ProjectArg = Annotated[ProjectId, Argument(help="Project ID", show_default=False, default_factory=ask_project)]


def _org_default():
    memberships = list(state.spiral.api.organizations.list_memberships())

    if not memberships:
        ERR_CONSOLE.print("No organizations found")
        raise typer.Exit(1)

    return choose(
        "Select an organization",
        choices=[
            Choice(
                title=f"{m.org.id} - {m.org.name}" if m.org.name else m.org.id,
                value=m.org.id,
            )
            for m in memberships
        ],
    )


OrganizationArg = Annotated[OrgId, Argument(help="Organization ID", show_default=False, default_factory=_org_default)]
