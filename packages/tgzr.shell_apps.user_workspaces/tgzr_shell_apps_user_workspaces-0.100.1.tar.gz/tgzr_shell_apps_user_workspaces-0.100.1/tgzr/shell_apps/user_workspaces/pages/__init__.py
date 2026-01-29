from __future__ import annotations
from typing import TYPE_CHECKING

from nicegui import ui, event

from tgzr.nice import layout
from tgzr.nice.controls.breadcrumbs import breadcrumbs

from ..components.settings import settings_dialog
from ..components.workspace_view import workspace_renderer

if TYPE_CHECKING:
    from ..app import UserWorkspaceAppState, UserWorkspacesSettings
    from tgzr.nice.tgzr_visid import TGZRVisId

    StateType = UserWorkspaceAppState[UserWorkspacesSettings]


async def hello_renderer(state: StateType):
    def set_studio(studio_name):
        state.data.crumbs.goto(studio_name)

    with ui.column(align_items="center").classes("w-full"):
        ui.label(f"Welcome {state.session.context.user_name}").classes("text-h2")
        ui.label("Which Studio are you working with today ?").classes("text-h4")
        with ui.grid(columns="auto auto auto"):
            for studio_name in state.session.workspace.studio_names():
                ui.button(
                    studio_name, on_click=lambda n=studio_name: set_studio(n)
                ).classes("opacity-50 hover:opacity-100")


async def studio_renderer(state: StateType):
    def set_project(project_name):
        state.data.crumbs.goto(state.session.context.studio_name, project_name)

    with ui.column(align_items="center").classes("w-full h-full"):
        ui.label(f"Welcome {state.session.context.user_name}").classes("text-h2")
        ui.label("Which Project are you working on ?").classes("text-h4")
        with ui.grid(columns="auto auto auto"):
            studio_name = state.session.context.studio_name
            if studio_name is None:
                ui.label(
                    "Hmmm... this is ackward. You don't have any studio selected..."
                )
                return

            studio = state.session.workspace.get_studio(
                studio_name, ensure_exists=False
            )
            if studio is None:
                ui.label(
                    f"Hmmmm... This is ackward. The studio {studio_name} was not found..."
                )
                return

            for project_name in studio.get_project_names():
                ui.button(
                    project_name, on_click=lambda n=project_name: set_project(n)
                ).classes("opacity-50 hover:opacity-100")
        with ui.row(align_items="end").classes("w-full h-full p-10"):
            ui.space()
            ui.button("Change Studio", on_click=lambda: state.data.crumbs.goto()).props(
                "flat"
            )
            ui.space()


async def test_movabales():

    from tgzr.nice.layout.movable import MovableContainer, Movable

    class Node(ui.element):
        def __init__(self, x=0, y=0, nb_children: int = 4):
            super().__init__()
            self.nb_children = nb_children
            self.x = x
            self.y = y

        async def build(self):
            with self:
                with Movable(self.x, self.y) as self.movable:
                    with ui.row(align_items="start", wrap=False):
                        # with MovableContainer(min_height=1, min_width=1).classes(
                        #     "border-2 border-dashed rounded-xl"
                        # ):
                        self.cparent = ui.column().classes("border border-dashed")
                    ui.button("+", on_click=self.open)
                    ui.label("Title").classes("text-xl border")

        async def open(self):
            with self.cparent:
                cx = 100
                cy = 0
                for i in range(self.nb_children):
                    n = Node(cx, cy, self.nb_children - 1)
                    await n.build()
                    w, h = await n.movable.size()
                    cy += h or 0

    with ui.column(align_items="center").classes("w-full"):
        with MovableContainer().classes("border-2 border-dashed rounded-xl rtl"):
            n = Node()
            await n.build()
            # with Movable(x=50, y=50):
            #     with ui.card().tight():
            #         ui.label("Box 1").classes("text-xl font-bold p-4")
            #         ui.separator()
            #         with ui.card_section():
            #             ui.label("Regular NiceGUI card")

            # with Movable(x=200, y=100):
            #     with ui.card().tight():
            #         ui.label("Box 2").classes("text-xl font-bold p-4")
            #         ui.separator()
            #         with ui.card_section():
            #             ui.button(
            #                 "Click me", on_click=lambda: ui.notify("Button clicked!")
            #             )

            # with Movable(x=100, y=200).classes("border border-blue-300"):
            #     with ui.row(align_items="center", wrap=False):
            #         with MovableContainer(min_height=1, min_width=1).classes(
            #             "border-2 border-dashed rounded-xl"
            #         ):
            #             with Movable(x=0, y=0):
            #                 with ui.card().tight():
            #                     ui.label("Box 3").classes("text-xl font-bold p-4")
            #                     ui.separator()
            #                     with ui.card_section():
            #                         ui.input("Type here", value="Interactive!")

            #             with Movable(x=20, y=100):
            #                 with ui.card().tight():
            #                     ui.label("Box 4").classes("text-xl font-bold p-4")
            #                     ui.separator()
            #                     with ui.card_section():
            #                         with ui.row(wrap=False):
            #                             ui.switch("Toggle me", value=True)
            #                             ui.checkbox("Check me too!")
            #         ui.label("Title").classes("text-xl")


async def project_renderer(state: StateType):
    def set_workspace(workspace_name):
        state.data.crumbs.goto(
            state.session.context.studio_name,
            state.session.context.project_name,
            workspace_name,
        )

    # await test_movabales()
    # return

    with ui.column(align_items="center").classes("w-full h-full"):
        ui.label(f"Welcome {state.session.context.user_name}").classes("text-h2")
        studio_name = state.session.context.studio_name
        if studio_name is None:
            ui.label("Hmmm... this is ackward. You don't have any studio selected...")
            return

        project_name = state.session.context.studio_name
        if project_name is None:
            ui.label("Hmmm... this is ackward. You don't have any studio selected...")
            return

        known_workspaces = await state.get_workspace_names()
        if not known_workspaces:
            ui.label("You don't have any workspace yet.").classes("text-h4")
            ui.button(
                "Create My First Workspace ✨",
                icon="sym_o_workspace_premium",
                on_click=lambda s=state: create_workspace(state),
            )
        else:
            ui.label("Select a Workspace:").classes("text-h4")
        with ui.grid(columns="auto auto auto"):
            for workspace_name in known_workspaces:
                ui.button(
                    workspace_name, on_click=lambda n=workspace_name: set_workspace(n)
                ).classes("opacity-50 hover:opacity-100")

        with ui.row(align_items="end").classes("w-full h-full p-10"):
            ui.space()
            ui.button(
                "Create New Workspace",
                icon="sym_o_add_circle",
                on_click=lambda s=state: create_workspace(state),
            ).props("flat")
            ui.button(
                "Import an existing Workspaces",
                icon="sym_o_download",
                on_click=lambda: ui.notify(
                    "Sorry, not Implemented. Wanny found us? 🤗", position="top"
                ),
            ).props("flat")
            ui.button(
                "Change Project",
                icon="sym_o_theaters",
                on_click=lambda: state.data.crumbs.goto(
                    state.session.context.studio_name
                ),
            ).props("flat")
            ui.button(
                "Change Studio",
                icon="sym_o_domain",
                on_click=lambda: state.data.crumbs.goto(),
            ).props("flat")
            ui.space()


async def create_workspace(state: StateType):
    with ui.dialog() as dialog, ui.card():

        def name_validate(value: str):
            if not value.replace("_", "").isalnum():
                return 'Only letter, number and "_" allowed'
            if not value[0].isalpha():
                return "First character must be a letter"
            if len(value) < 4:
                return "Too short"

        name_input = ui.input(label="Workspace Name", validation=name_validate)
        with ui.row().classes("w-full"):
            ui.space()
            ui.button("Create", on_click=lambda: dialog.submit(name_input.value))

    name = await dialog
    if name is None:
        return

    # state.session.broker.cmd(
    #     cmd_name="session.settings.edit",
    #     key=state.app.settings_key + ".workspace_names",
    #     context_name=state.session.context.user_name,
    #     op="append",
    #     value=name,
    # )
    await state.session.settings.append(
        context_name=state.session.context.user_name,
        name=state.app.settings_key + ".workspace_names",
        value=name,
    )

    new_settings = await state.app_settings(reload=True)
    state.workspace_name = name
    state.data.crumbs.goto(
        state.session.context.studio_name,
        state.session.context.project_name,
        name,
    )


class View:
    def __init__(self, state: StateType) -> None:
        self.state = state
        self._views = dict(
            hello=hello_renderer,
            studio=studio_renderer,
            project=project_renderer,
            workspace=workspace_renderer,
        )
        self._view_name = None
        self._view_changed_event = event.Event()
        self._view_changed_event.subscribe(self.render.refresh)

    def set_view(self, view_name: str):
        self._view_name = view_name
        self._view_changed_event.emit()

    @ui.refreshable_method
    async def render(self):
        view = self._views.get(self._view_name, hello_renderer)  # type: ignore
        await view(self.state)


class NavigationCrumbs:
    def __init__(self, view: View) -> None:
        self.view = view
        self.state = view.state
        self._breadcrumbs = None

    @ui.refreshable_method
    def render(self):
        path = self.current_path()
        self._breadcrumbs = breadcrumbs(
            crumbs=path,  # type: ignore
            on_changed=self._on_path_changed,
        )
        if len(path) == 2:
            self._breadcrumbs.set_icons("sym_o_domain", "sym_o_theaters")
        else:
            self._breadcrumbs.set_icons(
                "sym_o_domain", "sym_o_palette", "sym_o_theaters"
            )

    def current_path(self) -> list[str]:
        path = []
        context = self.state.session.context

        if context.studio_name is None:
            return path
        path.append(context.studio_name)

        if context.project_name is None:
            return path
        path.append(context.project_name)

        if self.state.workspace_name is None:
            return path
        path.append(self.state.workspace_name)

        return path

    def _on_path_changed(self, new_path: list[str]):
        self.goto(*new_path)

    def goto(self, *crumbs: str):
        context = self.state.session.context
        path = list(crumbs)

        studio = path and path.pop(0) or None
        context.studio_name = studio  # type: ignore

        project = path and path.pop(0) or None
        context.project_name = project  # type: ignore

        workspace = path and path.pop(0) or None
        self.state.workspace_name = workspace  # type: ignore

        self.render.refresh()  # pyright: ignore[reportAttributeAccessIssue]

        view = ("hello", "studio", "project", "workspace")[len(crumbs)]
        self.view.set_view(view)


@ui.page("/")
async def user_workspaces():
    from ..app import app

    state = app.create_app_state()
    await state.session.connect()

    view = View(state)
    crumbs = NavigationCrumbs(view)
    state.data.crumbs = crumbs
    state.data.render_all_event = event.Event()
    crumbs.goto(*crumbs.current_path())

    async def edit_settings():
        await settings_dialog(
            session=state.session,
            visid=state.visid,
            settings_context=state.app_settings_context,
            settings_key=state.app.settings_key,
            settings_defaults=await state.app_settings(reload=True),
            title="User Workspaces Settings",
        )
        # Re-read the settings model, which updates settings in State:
        await state.app_settings(reload=True)
        # Then re-render the whole page (is this really needed in our case?)
        await render_all.refresh()

    @ui.refreshable
    async def render_all():
        with layout.fullpage():
            with ui.row(align_items="center").classes("p-5 w-full"):
                state.visid.logo(classes="w-16")
                with ui.row(align_items="baseline").classes("grow"):
                    ui.label("TGZR").classes("text-5xl font-thin tracking-[1em]")
                    ui.label("User Workspaces").classes(
                        "text-2xl font-thin tracking-[1em]"
                    )
                    crumbs.render()
                ui.space()
                fullscreen = ui.fullscreen()
                ui.button(
                    icon="sym_o_fullscreen",
                    color="W",
                    on_click=fullscreen.toggle,
                ).props("flat")
                ui.button(icon="settings", color="W", on_click=edit_settings).props(
                    "flat size=1em"
                )

            with ui.row(wrap=False).classes("w-full h-full"):
                await view.render()

    await render_all()
    state.data.render_all_event.subscribe(render_all.refresh)
