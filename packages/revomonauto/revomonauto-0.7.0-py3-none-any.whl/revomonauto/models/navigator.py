"""Navigator module for route pathfinding and script execution."""

import logging
from collections import deque
from typing import TYPE_CHECKING

from revomonauto.models.route import RouteRegistry, get_default_registry

if TYPE_CHECKING:
    from revomonauto.models.location_tracker import LocationTracker


class Navigator:
    """Handles route navigation using pre-recorded movement scripts."""

    def __init__(
        self,
        controller,
        registry: RouteRegistry | None = None,
        location_tracker: "LocationTracker | None" = None,
    ):
        """Initialize the Navigator.

        Args:
            controller: RevomonController instance.
            registry: Optional RouteRegistry (defaults to loading from routes.yaml).
            location_tracker: Optional LocationTracker for auto-detection after routes.
        """
        self.controller = controller
        self.logger = logging.getLogger(__name__)
        self.registry = registry if registry is not None else get_default_registry()
        self.location_tracker = location_tracker

    def build_route_graph(self) -> dict:
        """Build a directed graph from registered routes (cached).

        Returns:
            Dict mapping (city, loc) -> {(target_city, target_loc): route_key}.
        """
        return self.registry.build_graph()

    def find_path(
        self,
        start_node: tuple[str, str],
        end_node: tuple[str, str],
        graph: dict | None = None,
    ) -> list[str] | None:
        """Find shortest path using BFS.

        Args:
            start_node: Tuple of (city, location).
            end_node: Tuple of (city, location).
            graph: Route graph (uses cached graph if None).

        Returns:
            List of route keys forming the path, or None if no path exists.
        """
        if graph is None:
            graph = self.build_route_graph()

        if start_node == end_node:
            return []

        # Use deque for O(1) popleft instead of list.pop(0)
        queue: deque[tuple[tuple[str, str], list[str]]] = deque([(start_node, [])])
        visited: set[tuple[str, str]] = set()

        while queue:
            vertex, path = queue.popleft()

            if vertex == end_node:
                return path

            if vertex in visited:
                continue
            visited.add(vertex)

            if vertex in graph:
                for neighbor, route_name in graph[vertex].items():
                    if neighbor not in visited:
                        queue.append((neighbor, path + [route_name]))

        return None

    def navigate_to(
        self,
        current_city: str,
        current_loc: str,
        dest_city: str,
        dest_loc: str,
    ) -> bool:
        """Navigate from current location to destination using available routes.

        Args:
            current_city: Current city name.
            current_loc: Current location within city.
            dest_city: Destination city name.
            dest_loc: Destination location within city.

        Returns:
            True if destination reached, False otherwise.
        """
        start_node = (current_city, current_loc)
        end_node = (dest_city, dest_loc)

        self.logger.info(
            f"Navigating from {current_city}-{current_loc} to {dest_city}-{dest_loc}"
        )

        if start_node == end_node:
            self.logger.info("Already at destination.")
            return True

        path = self.find_path(start_node, end_node)

        if not path:
            self.logger.error(f"No path found from {start_node} to {end_node}")
            return False

        self.logger.info(f"Path found: {len(path)} routes to destination.")

        for route_name in path:
            script = self.registry.get_script(route_name)

            if not script:
                self.logger.warning(
                    f"No script for route: {route_name}. Skipping move."
                )
            else:
                self.logger.info(f"Executing route: {route_name}")
                self.controller.execute_movement_script(script)

            # Update internal state from route name
            parts = route_name.split("_")
            if len(parts) >= 4:
                new_city, new_loc = parts[-2], parts[-1]
                self.controller.revomon.current_city = new_city
                self.controller.revomon.current_location = new_loc
                self.logger.info(f"Arrived at: {new_city}-{new_loc}")

        return True

    def navigate_to_closest(
        self,
        current_city: str,
        current_loc: str,
        target_loc_type: str,
    ) -> bool:
        """Find the closest node with location == target_loc_type and navigate to it.

        Args:
            current_city: Current city name.
            current_loc: Current location within city.
            target_loc_type: Target location type to find (e.g., 'insiderevocenter').

        Returns:
            True if navigation succeeded, False otherwise.
        """
        graph = self.build_route_graph()
        start_node = (current_city, current_loc)

        # BFS to find closest target
        queue: deque[tuple[tuple[str, str], list[str]]] = deque([(start_node, [])])
        visited: set[tuple[str, str]] = set()

        while queue:
            vertex, path = queue.popleft()

            if vertex[1] == target_loc_type:
                dest_city, dest_loc = vertex
                self.logger.info(
                    f"Closest {target_loc_type} found at {dest_city}-{dest_loc}"
                )
                return self.navigate_to(current_city, current_loc, dest_city, dest_loc)

            if vertex in visited:
                continue
            visited.add(vertex)

            if vertex in graph:
                for neighbor, route_name in graph[vertex].items():
                    if neighbor not in visited:
                        queue.append((neighbor, path + [route_name]))

        self.logger.error(f"No {target_loc_type} found reachable from {start_node}")
        return False

    def execute_route(self, route_name: str) -> bool:
        """Execute a single route using its movement script.

        Args:
            route_name: Route identifier.

        Returns:
            True if route executed successfully.
        """
        script = self.registry.get_script(route_name)
        if not script:
            self.logger.warning(f"No movement script for route: {route_name}")
            return False

        self.logger.info(f"Executing script for route: {route_name}")
        self.controller.execute_movement_script(script)
        return True

    def list_routes(self) -> list[str]:
        """List all available routes.

        Returns:
            Sorted list of route keys.
        """
        return self.registry.all_keys()

    def detect_current_location(self) -> tuple[str, str] | None:
        """Detect current location using the location tracker.

        Requires a LocationTracker to be configured during initialization.

        Returns:
            Tuple of (city, location) if detected, None otherwise.
        """
        if self.location_tracker is None:
            self.logger.warning(
                "No location tracker configured. Cannot detect location."
            )
            return None

        return self.location_tracker.detect_location()
