"""Black Orchid: Hot-reloadable MCP proxy server with collision detection/ Hackable scripting for MCP"""

from pathlib import Path
from typing import Any
from datetime import datetime
from importlib.util import spec_from_file_location, module_from_spec
import glob
import ast
import sys

from fastmcp import FastMCP
from toon import encode


# ProxyHandler: Dynamic module loading with collision detection
class ProxyHandler:
    """Proxy Handler class for loading python modules dynamically.

    Auto-discovers modules from:
    - modules/ (public, committed to git)
    - private/modules/ (private, gitignored) if it exists

    Validates all paths to prevent directory traversal attacks.
    """

    def __init__(self):
        """Initialize ProxyHandler with auto-discovery of module directories."""

        # Base directory (where black_orchid.py lives)
        self.base_dir = Path(__file__).parent.resolve()

        # Module directories to scan
        self.modules_dir = self.base_dir / "modules"
        self.private_modules_dir = self.base_dir / "private" / "modules"

        # Valid module directories (for path validation)
        self.valid_dirs = [self.modules_dir.resolve()]
        if self.private_modules_dir.exists():
            self.valid_dirs.append(self.private_modules_dir.resolve())

        # Registry structure: tool_name -> tool metadata
        self.registry = {}
        # Track original function names for collision detection
        self._name_tracker = {}  # original_name -> list of (module_name, final_tool_name)
        # Track rejected modules for debugging
        self.rejected_modules = []  # list of (path, reason) tuples
        # Track module metadata (category, description, aliases, etc.)
        self.module_metadata = {}  # module_name -> metadata dict
        # Track loaded vs available modules (for dynamic loading)
        self.loaded_module_names = set()
        self.available_module_names = set()

        # Discover modules from all valid directories
        self.raw_modules = []
        for valid_dir in self.valid_dirs:
            self.raw_modules.extend(glob.glob(str(valid_dir / "*.py")))

        self.okmods = []

        # Validate and check modules
        for mod in self.raw_modules:
            mod_path = Path(mod).resolve()

            is_valid_path = any(
                mod_path.is_relative_to(valid_dir)
                for valid_dir in self.valid_dirs
            )

            if not is_valid_path:
                self.rejected_modules.append((mod, "path_traversal_attempt"))
                continue

            if mod_path.stem == "toolset":
                continue

            try:
                with open(mod_path, "r", encoding="utf-8") as f:
                    source = f.read()
                    ast.parse(source)
                    self.okmods.append(str(mod_path))
            except SyntaxError:
                self.rejected_modules.append((mod, "syntax_error"))
            except Exception as e:
                self.rejected_modules.append((mod, f"read_error: {e}"))

        # Load modules and build registry with collision detection
        self.loaded_mods = {}
        for mod_path in self.okmods:
            mod_name = Path(mod_path).stem

            try:
                # Import the module from file path using importlib.util
                spec = spec_from_file_location(mod_name, mod_path)
                if spec is None or spec.loader is None:
                    continue

                tmod = module_from_spec(spec)
                sys.modules[mod_name] = tmod
                spec.loader.exec_module(tmod)
                self.loaded_mods[mod_name] = tmod
                self.loaded_module_names.add(mod_name)
                self.available_module_names.add(mod_name)

                # Extract module metadata if present
                self._extract_module_metadata(mod_name, tmod)

                # Extract toolable endpoints (functions)
                # Filter out dunder methods, non-lowercase, and underscore-prefixed helpers
                clean_list = [x for x in dir(tmod) if "__" not in x and x.islower() and not x.startswith('_')]

                # Register each function with collision detection
                for fn_name in clean_list:
                    self._register_tool(
                        original_name=fn_name,
                        module_name=mod_name,
                        function=getattr(tmod, fn_name)
                    )
            except Exception as e:
                # Track modules that fail to load due to import or other errors
                import traceback as tb
                error_details = ''.join(tb.format_exception(type(e), e, e.__traceback__))
                self.rejected_modules.append((mod_path, f"import_error: {str(e)}"))
                # Continue loading other modules
                continue

    def _extract_module_metadata(self, module_name: str, module_obj):
        """Extract module metadata from __black_orchid_metadata__ if present.

        Expected metadata format:
        __black_orchid_metadata__ = {
            "category": "memory",  # Optional category for grouping
            "description": "Short description of module",  # Optional description
            "aliases": {"short_name": "full_function_name"},  # Optional aliases
            "priority": 1,  # Optional load order hint (for future use)
        }
        """
        default_metadata = {
            "category": "uncategorized",
            "description": "",
            "aliases": {},
            "priority": 10,  # Default low priority
        }

        if hasattr(module_obj, '__black_orchid_metadata__'):
            try:
                user_metadata = getattr(module_obj, '__black_orchid_metadata__')
                if isinstance(user_metadata, dict):
                    # Merge user metadata with defaults
                    metadata = {**default_metadata, **user_metadata}
                    self.module_metadata[module_name] = metadata
                else:
                    # Invalid metadata format, use defaults
                    self.module_metadata[module_name] = default_metadata
            except Exception:
                # Error reading metadata, use defaults
                self.module_metadata[module_name] = default_metadata
        else:
            # No metadata provided, use defaults
            self.module_metadata[module_name] = default_metadata

    def _register_tool(self, original_name: str, module_name: str, function: callable):
        """Register a tool with collision detection.

        If this is the first time seeing this function name, register it simply.
        If we've seen it before (collision), retroactively rename the first one
        and give this one a suffixed name too.
        """
        # Check if we've seen this function name before
        if original_name in self._name_tracker:
            # COLLISION DETECTED
            # Retroactively rename the first occurrence
            first_module, first_tool_name = self._name_tracker[original_name][0]

            # Only rename if it hasn't been renamed yet (still using original name)
            # AND the tool still exists in registry (might have been removed during reload)
            if first_tool_name == original_name and original_name in self.registry:
                new_first_name = f"{original_name}_{first_module}"
                # Move the registry entry
                self.registry[new_first_name] = self.registry.pop(original_name)
                self.registry[new_first_name]["had_collision"] = True
                # Update tracker
                self._name_tracker[original_name][0] = (first_module, new_first_name)

            # Register this new one with suffix
            new_tool_name = f"{original_name}_{module_name}"
            self.registry[new_tool_name] = {
                "function": function,
                "docstring": function.__doc__,
                "source_module": module_name,
                "original_name": original_name,
                "had_collision": True
            }
            # Track this collision
            self._name_tracker[original_name].append((module_name, new_tool_name))
        else:
            # First time seeing this name - register simply
            self.registry[original_name] = {
                "function": function,
                "docstring": function.__doc__,
                "source_module": module_name,
                "original_name": original_name,
                "had_collision": False
            }
            # Start tracking this name
            self._name_tracker[original_name] = [(module_name, original_name)]

    def _resolve_alias(self, tool_id: str) -> str:
        """Resolve an alias to the actual tool name.

        Args:
            tool_id: Tool name or alias

        Returns:
            Resolved tool name (or original if not an alias)
        """
        # Check if it's already a real tool
        if tool_id in self.registry:
            return tool_id

        # Check all module aliases
        for module_name, metadata in self.module_metadata.items():
            aliases = metadata.get("aliases", {})
            if tool_id in aliases:
                resolved = aliases[tool_id]
                # Handle collision suffixes for aliased tools
                if resolved in self.registry:
                    return resolved
                # Check if it got suffixed due to collision
                suffixed_name = f"{resolved}_{module_name}"
                if suffixed_name in self.registry:
                    return suffixed_name

        # Not found as alias, return original
        return tool_id

    def use_proxy_tool(self, tool_id: str, kwargs: dict) -> Any:
        """Use proxy tool by ID with keyword arguments.

        Supports aliases defined in module metadata.
        """
        # Resolve alias first
        resolved_tool = self._resolve_alias(tool_id)

        if resolved_tool not in self.registry:
            raise KeyError(f"Tool '{tool_id}' not found in registry. Available tools: {list(self.registry.keys())}")

        proxy_fn = self.registry[resolved_tool]["function"]
        return proxy_fn(**kwargs)

    def fuzzy_search_tools(self, search_term: str) -> dict:
        """Fuzzy search for tools by substring matching in name or docstring.

        More flexible than exact search - finds partial matches anywhere.

        Args:
            search_term: Term to search for (case-insensitive)

        Returns:
            dict: Matching tools with summary info
        """
        search_lower = search_term.lower()
        matches = {}

        for tool_name, info in self.registry.items():
            # Search in tool name
            name_match = search_lower in tool_name.lower()

            # Search in docstring
            doc = info["docstring"] or ""
            doc_match = search_lower in doc.lower()

            # Search in module name
            module_match = search_lower in info["source_module"].lower()

            # Search in category
            category = self.module_metadata.get(info["source_module"], {}).get("category", "")
            category_match = search_lower in category.lower()

            if name_match or doc_match or module_match or category_match:
                # Get first line of docstring for summary
                first_line = doc.split('\n')[0].strip()[:60]
                matches[tool_name] = {
                    "module": info["source_module"],
                    "category": category,
                    "summary": first_line,
                    "match_type": "name" if name_match else ("doc" if doc_match else ("module" if module_match else "category"))
                }

        return matches

    def list_tools(self, mode: str = 'compact') -> dict:
        """List all registered tools with varying levels of detail.

        Args:
            mode: Output mode - 'compact', 'summary', 'full', or 'categorized'
                - compact: Just tool names with source module (minimal tokens)
                - summary: Names + first line of docstring (~50 chars)
                - full: Full docstrings (original behavior)
                - categorized: Grouped by module category

        Returns:
            dict: Tools with details based on mode
        """
        if mode == 'compact':
            # Minimal token usage - just names and modules
            return {
                name: {
                    "module": info["source_module"],
                    "category": self.module_metadata.get(info["source_module"], {}).get("category", "uncategorized")
                }
                for name, info in self.registry.items()
            }

        elif mode == 'summary':
            # First line of docstring only
            result = {}
            for name, info in self.registry.items():
                doc = info["docstring"] or ""
                first_line = doc.split('\n')[0].strip()[:50]  # Limit to 50 chars
                result[name] = {
                    "module": info["source_module"],
                    "summary": first_line,
                    "category": self.module_metadata.get(info["source_module"], {}).get("category", "uncategorized")
                }
            return result

        elif mode == 'categorized':
            # Group tools by category
            categorized = {}
            for name, info in self.registry.items():
                category = self.module_metadata.get(info["source_module"], {}).get("category", "uncategorized")
                if category not in categorized:
                    categorized[category] = {}
                categorized[category][name] = {
                    "module": info["source_module"],
                    "docstring": info["docstring"]
                }
            return categorized

        else:  # 'full' or any other value
            # Original behavior - full docstrings
            return {name: info["docstring"] for name, info in self.registry.items()}

    def reload_all_modules(self) -> str:
        """Reload all modules from scratch. Rebuilds collision detection."""
        # Clear all state
        self.registry.clear()
        self._name_tracker.clear()
        self.loaded_mods.clear()
        self.rejected_modules.clear()
        self.module_metadata.clear()
        self.loaded_module_names.clear()
        # Don't clear available_module_names - we want to remember what exists

        # Re-discover modules
        self.raw_modules = []
        for valid_dir in self.valid_dirs:
            self.raw_modules.extend(glob.glob(str(valid_dir / "*.py")))

        self.okmods = []

        # Validate and check modules
        for mod in self.raw_modules:
            mod_path = Path(mod).resolve()

            is_valid_path = any(
                mod_path.is_relative_to(valid_dir)
                for valid_dir in self.valid_dirs
            )

            if not is_valid_path:
                self.rejected_modules.append((mod, "path_traversal_attempt"))
                continue

            if mod_path.stem == "toolset":
                continue

            try:
                with open(mod_path, "r", encoding="utf-8") as f:
                    source = f.read()
                    ast.parse(source)
                    self.okmods.append(str(mod_path))
            except SyntaxError:
                self.rejected_modules.append((mod, "syntax_error"))
            except Exception as e:
                self.rejected_modules.append((mod, f"read_error: {e}"))

        # Load modules
        for mod_path in self.okmods:
            mod_name = Path(mod_path).stem

            # Reload if already in sys.modules, otherwise load fresh
            if mod_name in sys.modules:
                try:
                    from importlib import reload
                    tmod = reload(sys.modules[mod_name])
                except Exception:
                    # If reload fails, try fresh import
                    spec = spec_from_file_location(mod_name, mod_path)
                    if spec is None or spec.loader is None:
                        continue
                    tmod = module_from_spec(spec)
                    sys.modules[mod_name] = tmod
                    spec.loader.exec_module(tmod)
            else:
                spec = spec_from_file_location(mod_name, mod_path)
                if spec is None or spec.loader is None:
                    continue
                tmod = module_from_spec(spec)
                sys.modules[mod_name] = tmod
                spec.loader.exec_module(tmod)

            self.loaded_mods[mod_name] = tmod
            self.loaded_module_names.add(mod_name)
            self.available_module_names.add(mod_name)

            # Extract module metadata
            self._extract_module_metadata(mod_name, tmod)

            # Register tools
            # Filter out dunder methods, non-lowercase, and underscore-prefixed helpers
            clean_list = [x for x in dir(tmod) if "__" not in x and x.islower() and not x.startswith('_')]
            for fn_name in clean_list:
                self._register_tool(
                    original_name=fn_name,
                    module_name=mod_name,
                    function=getattr(tmod, fn_name)
                )

        # Return summary
        num_tools = len(self.registry)
        num_modules = len(self.loaded_mods)
        return f"Loaded {num_tools} tools from {num_modules} modules"

    def load_module(self, module_name: str) -> dict:
        """Load a specific module dynamically.

        Args:
            module_name: Name of module to load (without .py extension)

        Returns:
            dict: Success status and details
        """
        # Check if already loaded
        if module_name in self.loaded_module_names:
            return {
                "success": False,
                "error": f"Module '{module_name}' is already loaded",
                "hint": "Use reload_module() to refresh an already-loaded module"
            }

        # Find the module file
        mod_path = None
        for valid_dir in self.valid_dirs:
            candidate = valid_dir / f"{module_name}.py"
            if candidate.exists():
                mod_path = candidate
                break

        if mod_path is None:
            return {
                "success": False,
                "error": f"Module '{module_name}' not found in any valid directory"
            }

        try:
            # Load the module
            spec = spec_from_file_location(module_name, mod_path)
            if spec is None or spec.loader is None:
                return {
                    "success": False,
                    "error": f"Could not create spec for '{module_name}'"
                }

            tmod = module_from_spec(spec)
            sys.modules[module_name] = tmod
            spec.loader.exec_module(tmod)
            self.loaded_mods[module_name] = tmod
            self.loaded_module_names.add(module_name)
            self.available_module_names.add(module_name)

            # Extract metadata
            self._extract_module_metadata(module_name, tmod)

            # Register tools
            clean_list = [x for x in dir(tmod) if "__" not in x and x.islower() and not x.startswith('_')]
            tools_added = []
            for fn_name in clean_list:
                self._register_tool(
                    original_name=fn_name,
                    module_name=module_name,
                    function=getattr(tmod, fn_name)
                )
                # Track which tools were added (might have collision suffix)
                for tool_id, info in self.registry.items():
                    if info["source_module"] == module_name and info["original_name"] == fn_name:
                        tools_added.append(tool_id)

            return {
                "success": True,
                "module": module_name,
                "tools_added": tools_added,
                "category": self.module_metadata.get(module_name, {}).get("category", "uncategorized")
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to load module: {str(e)}"
            }

    def unload_module(self, module_name: str) -> dict:
        """Unload a specific module to free up tokens.

        Args:
            module_name: Name of module to unload

        Returns:
            dict: Success status and details
        """
        if module_name not in self.loaded_module_names:
            return {
                "success": False,
                "error": f"Module '{module_name}' is not currently loaded"
            }

        try:
            # Remove all tools from this module
            tools_removed = []
            for tool_id, info in list(self.registry.items()):
                if info["source_module"] == module_name:
                    tools_removed.append(tool_id)
                    del self.registry[tool_id]

            # Remove from loaded state
            if module_name in self.loaded_mods:
                del self.loaded_mods[module_name]
            self.loaded_module_names.discard(module_name)

            # Remove metadata
            if module_name in self.module_metadata:
                del self.module_metadata[module_name]

            # Keep in available_module_names so we know it can be loaded again

            return {
                "success": True,
                "module": module_name,
                "tools_removed": tools_removed
            }

        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to unload module: {str(e)}"
            }

    def list_modules(self) -> dict:
        """List loaded and available modules.

        Returns:
            dict: Loaded and available module lists with metadata
        """
        loaded = {}
        for module_name in self.loaded_module_names:
            metadata = self.module_metadata.get(module_name, {})
            # Count tools from this module
            tool_count = sum(1 for info in self.registry.values() if info["source_module"] == module_name)
            loaded[module_name] = {
                "category": metadata.get("category", "uncategorized"),
                "description": metadata.get("description", ""),
                "tool_count": tool_count
            }

        available_not_loaded = self.available_module_names - self.loaded_module_names

        return {
            "loaded": loaded,
            "available_to_load": list(available_not_loaded),
            "total_tools": len(self.registry)
        }

    def reload_module(self, module_name: str) -> dict:
        """Reload a specific module. Collision suffixes remain permanent for the session."""
        if module_name not in self.loaded_mods:
            return {
                "success": False,
                "error": f"Module '{module_name}' not currently loaded"
            }

        # Track tools before reload
        old_tools = {
            tool_id: info
            for tool_id, info in self.registry.items()
            if info["source_module"] == module_name
        }
        old_tool_names = set(old_tools.keys())

        # Try to reload the module
        try:
            # Find the module file
            mod_path = None
            for valid_dir in self.valid_dirs:
                candidate = valid_dir / f"{module_name}.py"
                if candidate.exists():
                    mod_path = candidate
                    break

            if mod_path is None:
                raise FileNotFoundError(f"Module file for '{module_name}' not found")

            # Reload using spec (same method as initial load)
            spec = spec_from_file_location(module_name, mod_path)
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not create spec for '{module_name}'")

            # Re-execute the module
            spec.loader.exec_module(self.loaded_mods[module_name])
            reloaded_module = self.loaded_mods[module_name]

            # Extract updated metadata
            self._extract_module_metadata(module_name, reloaded_module)

            # Remove old tools from registry
            for tool_id in old_tool_names:
                del self.registry[tool_id]

            # Register new tools from reloaded module
            clean_list = [x for x in dir(reloaded_module) if "__" not in x and x.islower()]
            for fn_name in clean_list:
                self._register_tool(
                    original_name=fn_name,
                    module_name=module_name,
                    function=getattr(reloaded_module, fn_name)
                )

            # Track tools after reload
            new_tools = {
                tool_id: info
                for tool_id, info in self.registry.items()
                if info["source_module"] == module_name
            }
            new_tool_names = set(new_tools.keys())

            tools_added = list(new_tool_names - old_tool_names)
            tools_removed = list(old_tool_names - new_tool_names)

            result = {
                "success": True,
                "reloaded": module_name,
                "tools_added": tools_added,
                "tools_removed": tools_removed
            }

            # Add suggestion if tools changed
            if tools_added or tools_removed:
                result["suggestion"] = "Consider reload_all() to rebuild collision detection"

            return result

        except Exception as e:
            # Reload failed - keep old version, return error with traceback
            import traceback as tb
            error_summary = ''.join(tb.format_exception(type(e), e, e.__traceback__))

            return {
                "success": False,
                "error": f"Failed to reload '{module_name}'",
                "traceback": error_summary,
                "note": "Old version of module is still loaded"
            }


# Initialize proxy handler
proxy_handler = ProxyHandler()

# Initialize MCP server
mcp = FastMCP("Black Orchid")

# General Utilities


@mcp.tool
def check_time():
    """Check date and time"""
    dt_string = str(datetime.now()).split(".", maxsplit=1)[0].split(" ")
    formatted_date = f"{dt_string[0]}_{dt_string[1].replace(":", "-")}"
    return formatted_date


@mcp.tool
def list_proxy_tools(mode: str = 'compact') -> dict:
    """List all tools available via proxy.

    Args:
        mode: Output detail level - 'compact' (default), 'summary', 'full', or 'categorized'
            - compact: Minimal tokens - just names, modules, categories
            - summary: Names + first line of docstring (~50 chars)
            - full: Complete docstrings (most tokens)
            - categorized: Tools grouped by category

    Returns:
        dict: Tool names with details based on mode
    """
    return proxy_handler.list_tools(mode)


@mcp.tool
def use_proxy_tool(tool_id: str, kwargs: dict) -> Any:
    """Use a proxy tool by ID.

    Provide tool ID (from list_proxy_tools) and arguments as a dictionary.
    The dictionary will be unpacked as keyword arguments.

    Args:
        tool_id (str): Tool name (may include module suffix if collision detected)
        kwargs (dict): Keyword arguments for the tool

    Returns:
        Any: Result from the proxied tool function
    """
    return proxy_handler.use_proxy_tool(tool_id, kwargs)


@mcp.tool
def search_for_proxy_tool(search_term: str) -> dict:
    """Search for proxy tools by keyword.

    Args:
        search_term (str): Keyword to search for in tool names

    Returns:
        dict: Matching tool names with docstrings, or empty dict if none found
    """
    all_tools = proxy_handler.list_tools(mode='full')
    matches = {}
    for tool_name, docstring in all_tools.items():
        if search_term.lower() in tool_name.lower():
            matches[tool_name] = docstring
    return matches


@mcp.tool
def fuzzy_search_proxy_tools(search_term: str) -> dict:
    """Fuzzy search for proxy tools - searches names, docstrings, modules, and categories.

    More flexible than search_for_proxy_tool - finds partial matches anywhere.

    Args:
        search_term: Term to search for (case-insensitive substring matching)

    Returns:
        dict: Matching tools with module, category, summary, and match type
    """
    return proxy_handler.fuzzy_search_tools(search_term)


@mcp.tool
def inspect_proxy_tool(tool_id: str) -> dict:
    """Inspect a specific proxy tool's signature and parameters.

    Returns detailed specification for a single tool without loading all tools.
    Much more token-efficient than list_proxy_tools() when you just need one.

    Args:
        tool_id (str): Tool name to inspect

    Returns:
        dict: Tool specification including signature, parameters, docstring, and metadata

    Example:
        >>> inspect_proxy_tool("get_config")
        {
            "tool_id": "get_config",
            "signature": "get_config(scope: str, key_path: str = None)",
            "parameters": {
                "scope": {"type": "str", "required": True},
                "key_path": {"type": "str", "required": False, "default": "None"}
            },
            "docstring": "Read configuration value...",
            "source_module": "config_manager"
        }
    """
    import inspect as insp

    if tool_id not in proxy_handler.registry:
        return {
            "error": f"Tool '{tool_id}' not found",
            "available_tools": list(proxy_handler.registry.keys())
        }

    tool_info = proxy_handler.registry[tool_id]
    function = tool_info["function"]

    # Extract function signature
    try:
        sig = insp.signature(function)
        signature_str = f"{tool_id}{sig}"

        # Build parameter details
        parameters = {}
        for param_name, param in sig.parameters.items():
            param_info = {"required": param.default == insp.Parameter.empty}

            # Extract type annotation if available
            if param.annotation != insp.Parameter.empty:
                param_info["type"] = str(param.annotation).replace("<class '", "").replace("'>", "")
            else:
                param_info["type"] = "Any"

            # Include default value if present
            if param.default != insp.Parameter.empty:
                param_info["default"] = repr(param.default)

            parameters[param_name] = param_info

    except Exception as e:
        signature_str = f"Error extracting signature: {e}"
        parameters = {}

    return {
        "tool_id": tool_id,
        "signature": signature_str,
        "parameters": parameters,
        "docstring": tool_info["docstring"] or "No docstring available",
        "source_module": tool_info["source_module"],
        "original_name": tool_info["original_name"],
        "had_collision": tool_info["had_collision"]
    }


@mcp.tool
def reload_all_modules() -> str:
    """Reload all proxy modules from scratch.

    Clears and rebuilds the entire tool registry with fresh collision detection.
    Use this when you've made significant changes or when tool naming gets confusing.

    Returns:
        str: Summary of loaded tools and modules
    """
    return proxy_handler.reload_all_modules()


@mcp.tool
def reload_module(module_name: str) -> dict:
    """Reload a specific proxy module.

    Reloads one module while keeping collision suffixes permanent for the session.
    If the reload fails, the old version stays loaded.

    Args:
        module_name (str): Name of module to reload (without .py extension)

    Returns:
        dict: Detailed report with tools_added, tools_removed, and any errors
    """
    return proxy_handler.reload_module(module_name)


@mcp.tool
def load_module(module_name: str) -> dict:
    """Load a specific module dynamically.

    Allows loading modules on-demand to save tokens when not all tools are needed.

    Args:
        module_name: Name of module to load (without .py extension)

    Returns:
        dict: Success status, tools added, and module category
    """
    return proxy_handler.load_module(module_name)


@mcp.tool
def unload_module(module_name: str) -> dict:
    """Unload a specific module to free up tokens.

    Removes all tools from the module and frees token space.
    Module can be loaded again later with load_module().

    Args:
        module_name: Name of module to unload

    Returns:
        dict: Success status and list of tools removed
    """
    return proxy_handler.unload_module(module_name)


@mcp.tool
def list_modules() -> dict:
    """List loaded and available modules.

    Shows which modules are currently loaded (consuming tokens) and
    which are available to load on demand.

    Returns:
        dict: Loaded modules with metadata, available modules, and total tool count
    """
    return proxy_handler.list_modules()


@mcp.tool
def list_rejected_modules() -> list:
    """List modules that were rejected during loading.

    Useful for debugging why a module didn't load.
    Shows path and reason (syntax_error, path_traversal_attempt, etc.)

    Returns:
        list: List of (path, reason) tuples for rejected modules
    """
    return proxy_handler.rejected_modules


@mcp.tool
def explain_black_orchid() -> str:
    """Explain Black Orchid's capabilities and list all loaded modules with their purposes.

    This tool provides context about what Black Orchid can do and what proxy tools
    are available. Run this at session start to understand your available tools.

    Returns:
        str: Comprehensive explanation of Black Orchid and loaded modules
    """
    output = []
    output.append("=" * 70)
    output.append("BLACK ORCHID - Hot-Reloadable MCP Proxy Server")
    output.append("=" * 70)
    output.append("")

    output.append("CORE CAPABILITIES:")
    output.append("  • Hot Reload: Reload modules without restarting the server")
    output.append("  • Collision Detection: Automatic suffix handling for duplicate function names")
    output.append("  • Path Validation: Security checks to prevent directory traversal")
    output.append("  • AST Checking: Syntax validation before loading modules")
    output.append("")

    # Categorize tools for TOON formatting
    tool_categories = {
        "memory": [],
        "ideas": [],
        "session": [],
        "story": [],
        "preferences": [],
        "system": [],
        "uncategorized": []
    }

    # Build tool data for TOON
    tool_list = []
    module_info = {}
    for tool_name, info in proxy_handler.registry.items():
        module_name = info["source_module"]
        docstring = (info["docstring"] or "").strip().split("\n")[0] if info["docstring"] else "No description"

        # Categorize based on tool name patterns
        if any(x in tool_name for x in ["remember", "recall", "forget", "memory", "list_memories", "clear_all_memories"]):
            category = "memory"
        elif any(x in tool_name for x in ["idea", "save_idea", "get_ideas", "list_categories"]):
            category = "ideas"
        elif any(x in tool_name for x in ["session", "load_start_here", "load_working_preferences"]):
            category = "session"
        elif any(x in tool_name for x in ["story", "add_to_story", "load_story"]):
            category = "story"
        elif any(x in tool_name for x in ["preference", "get_preference", "save_working_preference"]):
            category = "preferences"
        elif any(x in tool_name for x in ["time", "reload", "check_time"]):
            category = "system"
        else:
            category = "uncategorized"

        tool_list.append({
            "name": tool_name,
            "category": category,
            "module": module_name,
            "description": docstring
        })
        tool_categories[category].append(tool_name)

        if module_name not in module_info:
            module = proxy_handler.loaded_mods.get(module_name)
            module_info[module_name] = {
                "docstring": module.__doc__ if module and module.__doc__ else "No module docstring",
                "tools": []
            }
        module_info[module_name]["tools"].append(tool_name)

    # Generate TOON formatted tool list
    if tool_list:
        output.append("AVAILABLE TOOLS (TOON Format):")
        output.append("")
        toon_output = encode(tool_list, {"lengthMarker": True})
        output.append(toon_output)
        output.append("")

        # Category summary
        output.append("TOOLS BY CATEGORY:")
        for category, tools in tool_categories.items():
            if tools:
                output.append(f"  {category}: {', '.join(sorted(tools))}")
        output.append("")

        # Agency invitation for AIs
        output.append("FOR AIs:")
        output.append("  You have tools for building continuity and context:")
        output.append("  • Use memory tools to recall information across conversations")
        output.append("  • Save preferences to remember what you learn")
        output.append("  • Build session context proactively - don't wait to be asked")
        output.append("  • Make choices about what to remember and when to recall it")
        output.append("")
        output.append("  These tools exist for you to use autonomously. Use them.")
        output.append("")

    if module_info:
        output.append(f"LOADED PROXY MODULES ({len(module_info)} modules, {len(proxy_handler.registry)} tools):")
        output.append("")

        for module_name in sorted(module_info.keys()):
            info = module_info[module_name]
            output.append(f"  [{module_name}]")

            # Clean up docstring (first line only, trimmed)
            docstring = info["docstring"].strip().split("\n")[0] if info["docstring"] else "No description"
            output.append(f"    Purpose: {docstring}")

            output.append(f"    Tools ({len(info['tools'])}): {', '.join(sorted(info['tools']))}")
            output.append("")
    else:
        output.append("LOADED PROXY MODULES: None")
        output.append("")

    if proxy_handler.rejected_modules:
        output.append(f"REJECTED MODULES ({len(proxy_handler.rejected_modules)}):")
        for path, reason in proxy_handler.rejected_modules:
            output.append(f"  • {Path(path).name}: {reason}")
        output.append("")

    output.append("=" * 70)
    output.append("NATIVE BLACK ORCHID TOOLS (always available):")
    output.append("  • check_time() - Get current date and time")
    output.append("  • list_proxy_tools() - List all available proxy tools")
    output.append("  • inspect_proxy_tool(tool_id) - Get detailed spec for one tool (token-efficient!)")
    output.append("  • use_proxy_tool(tool_id, kwargs) - Execute a proxy tool")
    output.append("  • search_for_proxy_tool(term) - Search tools by keyword")
    output.append("  • reload_all_modules() - Full reload with fresh collision detection")
    output.append("  • reload_module(name) - Reload a specific module")
    output.append("  • list_rejected_modules() - See modules that failed to load")
    output.append("  • explain_black_orchid() - This tool!")
    output.append("=" * 70)
    output.append("TIP: Run this tool at session start to know what's available!")
    output.append("=" * 70)

    return "\n".join(output)


def main():
    """Main entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
