"""Route dataclass and registry for type-safe route representation.

This module provides a frozen dataclass representing a navigation route
with computed properties for graph building, plus a registry with YAML
persistence supporting compact format, shared scripts, and bidirectional routes.
"""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import yaml


@dataclass(frozen=True)
class Route:
    """Represents a navigation route between two locations.

    Attributes:
        start_city: Origin city identifier.
        start_location: Origin location within the city.
        end_city: Destination city identifier.
        end_location: Destination location within the city.
        script: Movement script as tuple of (angle, speed, duration) tuples.
    """

    start_city: str
    start_location: str
    end_city: str
    end_location: str
    script: tuple[tuple[float, float, float], ...] = field(default_factory=tuple)

    @property
    def key(self) -> str:
        """Generate the route key for registry lookups.

        Returns:
            Route key in format: start_city_start_location_end_city_end_location
        """
        return f"{self.start_city}_{self.start_location}_{self.end_city}_{self.end_location}"

    @property
    def start_node(self) -> tuple[str, str]:
        """Get the start node for graph building.

        Returns:
            Tuple of (start_city, start_location).
        """
        return (self.start_city, self.start_location)

    @property
    def end_node(self) -> tuple[str, str]:
        """Get the end node for graph building.

        Returns:
            Tuple of (end_city, end_location).
        """
        return (self.end_city, self.end_location)

    def reverse(
        self, script: tuple[tuple[float, float, float], ...] | None = None
    ) -> "Route":
        """Create a reversed route (swap start and end).

        Args:
            script: Optional script for reverse direction. If None, uses empty script.

        Returns:
            New Route with start/end swapped.
        """
        return Route(
            start_city=self.end_city,
            start_location=self.end_location,
            end_city=self.start_city,
            end_location=self.start_location,
            script=script if script is not None else (),
        )

    def __repr__(self) -> str:
        """Return a concise string representation."""
        return f"Route({self.key})"


class RouteRegistry:
    """Central registry for navigation routes.

    Provides registration, lookup, and YAML persistence for Route objects.
    Supports compact YAML format with shared scripts and bidirectional routes.

    Attributes:
        logger: Logger instance for this registry.
    """

    def __init__(self, config_path: Path | None = None):
        """Initialize the route registry.

        Args:
            config_path: Optional path to YAML config file to load routes from.
        """
        self._routes: dict[str, Route] = {}
        self._scripts: dict[str, tuple[tuple[float, float, float], ...]] = {}
        self._graph_cache: dict | None = None
        self.logger = logging.getLogger(__name__)

        if config_path is not None:
            self.load_from_yaml(config_path)

    def register(self, route: Route) -> None:
        """Register a route in the registry.

        Args:
            route: Route object to register.
        """
        self._routes[route.key] = route
        self._graph_cache = None  # Invalidate cache
        self.logger.debug(f"Registered route: {route.key}")

    def unregister(self, key: str) -> bool:
        """Remove a route from the registry.

        Args:
            key: Route key to unregister.

        Returns:
            True if route was removed, False if not found.
        """
        if key in self._routes:
            del self._routes[key]
            self._graph_cache = None  # Invalidate cache
            self.logger.debug(f"Unregistered route: {key}")
            return True
        return False

    def get(self, key: str) -> Route | None:
        """Get a route by its key.

        Args:
            key: Route key in format start_city_start_loc_end_city_end_loc.

        Returns:
            Route object or None if not found.
        """
        return self._routes.get(key)

    def get_script(self, key: str) -> tuple[tuple[float, float, float], ...] | None:
        """Get the movement script for a route or shared script.

        Args:
            key: Route key or shared script name to look up.

        Returns:
            Movement script tuple or None if not found.
        """
        # First check routes
        route = self.get(key)
        if route:
            return route.script
        # Then check shared scripts
        if key in self._scripts:
            return self._scripts[key]
        return None

    def has_route(self, key: str) -> bool:
        """Check if a route exists in the registry.

        Args:
            key: Route key to check.

        Returns:
            True if route exists, False otherwise.
        """
        return key in self._routes

    def all_routes(self) -> list[Route]:
        """Get all registered routes.

        Returns:
            List of all Route objects in the registry.
        """
        return list(self._routes.values())

    def all_keys(self) -> list[str]:
        """Get all route keys.

        Returns:
            Sorted list of all route keys.
        """
        return sorted(self._routes.keys())

    def build_graph(self) -> dict:
        """Build a cached directed graph from registered routes.

        Returns:
            Dict mapping (city, loc) -> {(target_city, target_loc): route_key}.
        """
        if self._graph_cache is not None:
            return self._graph_cache

        graph: dict[tuple[str, str], dict[tuple[str, str], str]] = {}
        for route in self._routes.values():
            origin = route.start_node
            dest = route.end_node
            if origin not in graph:
                graph[origin] = {}
            graph[origin][dest] = route.key

        self._graph_cache = graph
        return graph

    def __iter__(self) -> Iterator[Route]:
        """Iterate over all routes."""
        return iter(self._routes.values())

    def __len__(self) -> int:
        """Return the number of registered routes."""
        return len(self._routes)

    def __contains__(self, key: str) -> bool:
        """Check if a route key is in the registry."""
        return key in self._routes

    def _resolve_script(
        self, script_ref: str | list
    ) -> tuple[tuple[float, float, float], ...]:
        """Resolve a script reference or inline script to tuple format.

        Args:
            script_ref: Either a string (script name) or list of movements.

        Returns:
            Script as tuple of tuples.
        """
        if isinstance(script_ref, str):
            # Reference to shared script
            if script_ref in self._scripts:
                return self._scripts[script_ref]
            self.logger.warning(f"Unknown script reference: {script_ref}")
            return ()
        elif isinstance(script_ref, list):
            return tuple(tuple(move) for move in script_ref)
        return ()

    def load_from_yaml(self, path: Path) -> int:
        """Load routes from a YAML configuration file.

        Supports both legacy and compact formats:
        - Legacy: start_city, start_location, end_city, end_location fields
        - Compact: from/to arrays, shared scripts, bidirectional flag

        Args:
            path: Path to the YAML file.

        Returns:
            Number of routes loaded.

        Raises:
            FileNotFoundError: If the YAML file does not exist.
            yaml.YAMLError: If the YAML file is malformed.
        """
        if not path.exists():
            raise FileNotFoundError(f"Routes config not found: {path}")

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            self.logger.warning(f"Empty config file: {path}")
            return 0

        # Load shared scripts first
        if "scripts" in data:
            for name, script_list in data["scripts"].items():
                self._scripts[name] = tuple(tuple(move) for move in script_list)
            self.logger.debug(f"Loaded {len(self._scripts)} shared scripts")

        if "routes" not in data:
            self.logger.warning(f"No routes found in {path}")
            return 0

        count = 0
        for route_data in data["routes"]:
            # Compact format: from/to arrays
            if "from" in route_data and "to" in route_data:
                start_city, start_loc = route_data["from"]
                end_city, end_loc = route_data["to"]
            # Legacy format: individual fields
            else:
                start_city = route_data["start_city"]
                start_loc = route_data["start_location"]
                end_city = route_data["end_city"]
                end_loc = route_data["end_location"]

            # Resolve script
            script_ref = route_data.get("script", [])
            script = self._resolve_script(script_ref)

            route = Route(
                start_city=start_city,
                start_location=start_loc,
                end_city=end_city,
                end_location=end_loc,
                script=script,
            )
            self.register(route)
            count += 1

            # Handle bidirectional
            if route_data.get("bidirectional"):
                reverse_script_ref = route_data.get("reverse_script", [])
                reverse_script = self._resolve_script(reverse_script_ref)
                reverse_route = route.reverse(reverse_script)
                self.register(reverse_route)
                count += 1

        self.logger.info(f"Loaded {count} routes from {path}")
        return count

    def save_to_yaml(self, path: Path, compact: bool = True) -> int:
        """Save all routes to a YAML configuration file.

        Args:
            path: Path to save the YAML file.
            compact: If True, use compact from/to format.

        Returns:
            Number of routes saved.
        """
        routes_data = []
        for route in sorted(self._routes.values(), key=lambda r: r.key):
            if compact:
                route_dict = {
                    "from": [route.start_city, route.start_location],
                    "to": [route.end_city, route.end_location],
                }
            else:
                route_dict = {
                    "start_city": route.start_city,
                    "start_location": route.start_location,
                    "end_city": route.end_city,
                    "end_location": route.end_location,
                }
            route_dict["script"] = (
                [list(move) for move in route.script] if route.script else []
            )
            routes_data.append(route_dict)

        output: dict = {}
        if self._scripts:
            output["scripts"] = {
                name: [list(move) for move in script]
                for name, script in self._scripts.items()
            }
        output["routes"] = routes_data

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(output, f, default_flow_style=False, sort_keys=False)

        self.logger.info(f"Saved {len(routes_data)} routes to {path}")
        return len(routes_data)


def get_default_registry() -> RouteRegistry:
    """Get the default route registry loaded from routes.yaml.

    Returns:
        RouteRegistry with routes loaded from the default config file.
    """
    config_path = Path(__file__).parent.parent / "data" / "routes.yaml"
    if config_path.exists():
        return RouteRegistry(config_path)
    return RouteRegistry()
