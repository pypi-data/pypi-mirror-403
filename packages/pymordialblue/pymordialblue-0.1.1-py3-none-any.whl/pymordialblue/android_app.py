"""Core application logic for Pymordial."""

from pymordial.core.app import PymordialApp
from pymordial.core.controller import PymordialController
from pymordial.core.screen import PymordialScreen
from pymordial.core.state_machine import AppState
from pymordial.ui.element import PymordialElement


class PymordialAndroidApp(PymordialApp):
    """Represents an Android application with lifecycle management.

    The PymordialController reference is automatically set when this app
    is registered with a controller via PymordialController(apps=[...]) or
    controller.add_app(...).

    Attributes:
        app_name: The display name of the app.
        package_name: The Android package name (e.g., com.example.app).
        pymordial_controller: The controller managing this app.
        screens: A dictionary of screens belonging to this app.
        app_state: The state machine managing the app's lifecycle.
        ready_element: Optional element to detect when app is fully loaded.
            When this element becomes visible, app automatically transitions to READY.
    """

    def __init__(
        self,
        app_name: str,
        package_name: str,
        screens: dict[str, PymordialScreen] | dict = {},
        ready_element: PymordialElement | None = None,
    ) -> None:
        """Initializes a PymordialApp.

        Args:
            app_name: The display name of the app.
            package_name: The Android package name.
            screens: Optional dictionary of screens.
            ready_element: Optional element that indicates app is ready.
                When this element becomes visible after opening the app,
                the state will automatically transition from LOADING to READY.
                Example: main menu button, game title text, etc.

        Raises:
            ValueError: If app_name or package_name are empty.
        """
        if not app_name:
            raise ValueError("app_name must be a non-empty string")
        if not package_name:
            raise ValueError("package_name must be a non-empty string")
        super().__init__(app_name, screens, ready_element)

        self.package_name: str = package_name
        self.pymordial_controller: PymordialController | None = None

    def check_ready(self, max_tries: int = None) -> bool:
        """Check if ready_element is visible and transition to READY if so.

        This is automatically called after open() if ready_element is defined.
        You can also manually poll this to check loading status.

        Args:
            max_tries: Maximum detection attempts (default: None).

        Returns:
            True if transitioned to READY, False if still loading.

        Example:
            # Manual polling in a loop
            while app.is_loading():
                if app.check_ready():
                    print("App is ready!")
                    break
                time.sleep(0.5)
        """
        if not self.ready_element or not self.pymordial_controller:
            return False

        if self.app_state.current_state != AppState.LOADING:
            return False  # Only transition from LOADING

        # Check if ready element is visible
        try:
            if self.pymordial_controller.is_element_visible(
                self.ready_element, max_tries=max_tries
            ):
                self.app_state.transition_to(AppState.READY)
                return True
        except Exception:
            pass  # Element not visible yet

        return False

    def is_open(self) -> bool:
        """Checks if the app is in the READY state.

        Returns:
            True if the app is READY, False otherwise.
        """
        return self.app_state.current_state == AppState.READY

    def is_loading(self) -> bool:
        """Checks if the app is in the LOADING state.

        Apps remain in LOADING until:
        1. A ready_element becomes visible (automatic transition), or
        2. You manually transition: app.app_state.transition_to(AppState.READY)

        Returns:
            True if the app is LOADING, False otherwise.
        """
        return self.app_state.current_state == AppState.LOADING

    def is_closed(self) -> bool:
        """Checks if the app is in the CLOSED state.

        Returns:
            True if the app is CLOSED, False otherwise.
        """
        return self.app_state.current_state == AppState.CLOSED

    def __repr__(self) -> str:
        """Returns a string representation of the app."""
        return (
            f"PymordialApp("
            f"app_name='{self.app_name}', "
            f"package_name='{self.package_name}', "
            f"state={self.app_state.current_state.name})"
        )
