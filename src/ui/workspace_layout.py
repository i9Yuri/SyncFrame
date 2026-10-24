"""Workspace layout manager for customizable dashboard arrangement and persistence."""

import logging
from typing import Any, Dict, Optional

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QFrame, QGridLayout, QWidget

logger = logging.getLogger(__name__)


class WorkspaceLayoutManager:
    """
    Manages custom layout persistence, drag/reorder indicators, and grid positioning:
    - Allows switching between static operational mode and layout customization mode
    - Persists widget positions (row, col, row_span, col_span) via QSettings
    - Verifies bounds and falls back to deterministic defaults on invalid or missing configurations
    """

    DEFAULT_POSITIONS: Dict[str, Dict[str, int]] = {
        "drop_zone": {"row": 0, "col": 0, "row_span": 1, "col_span": 1},
        "card_remux_exec": {"row": 1, "col": 0, "row_span": 1, "col_span": 1},
        "card_acoustic": {"row": 0, "col": 1, "row_span": 1, "col_span": 1},
        "sync_controls": {"row": 1, "col": 1, "row_span": 1, "col_span": 1},
        "preview_player": {"row": 2, "col": 1, "row_span": 1, "col_span": 1},
    }

    def __init__(
        self,
        parent_grid: Optional[QGridLayout] = None,
        settings_group: str = "WorkspaceLayout",
        widgets_map: Optional[Dict[str, QWidget]] = None
    ):
        self.parent_grid = parent_grid
        self.settings = QSettings("SyncFrame", settings_group)
        self.widgets_map: Dict[str, QWidget] = widgets_map or {}
        self.is_edit_mode: bool = False

    def register_widgets(self, widgets_map: Dict[str, QWidget]) -> None:
        """Registers the dictionary of manageable workspace widgets."""
        self.widgets_map.update(widgets_map)

    def save_layout(self, widgets_map: Dict[str, QWidget]) -> None:
        """
        Persists grid geometry and coordinates for all active workspace cards.
        Contract: WorkspaceLayoutManager.save_layout(widgets_map: Dict[str, QWidget]) -> None
        """
        self.widgets_map.update(widgets_map)
        self.settings.beginGroup("cards")

        for name, widget in widgets_map.items():
            if not widget:
                continue

            self.settings.beginGroup(name)

            # Determine grid position from parent_grid if available or widget properties
            row = widget.property("_grid_row")
            col = widget.property("_grid_col")
            row_span = widget.property("_row_span")
            col_span = widget.property("_col_span")

            if self.parent_grid:
                idx = self.parent_grid.indexOf(widget)
                if idx >= 0:
                    r, c, rs, cs = self.parent_grid.getItemPosition(idx)
                    row, col, row_span, col_span = r, c, rs, cs

            # Fallback to defaults if not assigned
            defaults = self.DEFAULT_POSITIONS.get(name, {"row": 0, "col": 0, "row_span": 1, "col_span": 1})
            row = row if row is not None else defaults["row"]
            col = col if col is not None else defaults["col"]
            row_span = row_span if row_span is not None else defaults["row_span"]
            col_span = col_span if col_span is not None else defaults["col_span"]

            self.settings.setValue("row", int(row))
            self.settings.setValue("col", int(col))
            self.settings.setValue("row_span", int(row_span))
            self.settings.setValue("col_span", int(col_span))

            geom = widget.geometry()
            self.settings.setValue("width", geom.width())
            self.settings.setValue("height", geom.height())

            self.settings.endGroup()

        self.settings.endGroup()
        self.settings.setValue("has_custom_layout", True)
        self.settings.sync()
        logger.info("Workspace layout saved successfully.")

    def restore_layout(self, parent_grid: QGridLayout) -> bool:
        """
        Restores saved card positions into parent_grid with boundary checks and fallback.
        Contract: WorkspaceLayoutManager.restore_layout(parent_grid: QGridLayout) -> bool
        Returns True if custom configuration was successfully restored, False on fallback.
        """
        self.parent_grid = parent_grid
        if not self.settings.value("has_custom_layout", False, type=bool):
            self.apply_default_layout(parent_grid)
            return False

        self.settings.beginGroup("cards")
        child_groups = self.settings.childGroups()
        if not child_groups:
            self.settings.endGroup()
            self.apply_default_layout(parent_grid)
            return False

        new_positions: Dict[str, Dict[str, int]] = {}
        valid = True
        for name in child_groups:
            self.settings.beginGroup(name)
            try:
                row = int(self.settings.value("row", -1))
                col = int(self.settings.value("col", -1))
                row_span = int(self.settings.value("row_span", 1))
                col_span = int(self.settings.value("col_span", 1))

                # Boundary sanity checks
                if not (0 <= row <= 10 and 0 <= col <= 5 and 1 <= row_span <= 10 and 1 <= col_span <= 5):
                    logger.warning("Invalid grid coordinates for card '%s': (%d, %d). Falling back.", name, row, col)
                    valid = False
                    break

                new_positions[name] = {
                    "row": row,
                    "col": col,
                    "row_span": row_span,
                    "col_span": col_span,
                }
            except (ValueError, TypeError) as exc:
                logger.warning("Corrupted settings for card '%s': %s. Falling back.", name, exc)
                valid = False
                break
            finally:
                self.settings.endGroup()

        self.settings.endGroup()

        if not valid:
            self.apply_default_layout(parent_grid)
            return False

        # Apply positions to grid
        for name, pos in new_positions.items():
            widget = self.widgets_map.get(name)
            if widget:
                # Remove if already placed in grid
                idx = parent_grid.indexOf(widget)
                if idx >= 0:
                    parent_grid.removeWidget(widget)
                parent_grid.addWidget(widget, pos["row"], pos["col"], pos["row_span"], pos["col_span"])
                widget.setProperty("_grid_row", pos["row"])
                widget.setProperty("_grid_col", pos["col"])
                widget.setProperty("_row_span", pos["row_span"])
                widget.setProperty("_col_span", pos["col_span"])

        logger.info("Custom workspace layout restored successfully.")
        return True

    def apply_default_layout(self, parent_grid: QGridLayout) -> None:
        """Applies deterministic default 2-column layout."""
        self.parent_grid = parent_grid
        for name, pos in self.DEFAULT_POSITIONS.items():
            widget = self.widgets_map.get(name)
            if widget:
                idx = parent_grid.indexOf(widget)
                if idx >= 0:
                    parent_grid.removeWidget(widget)
                parent_grid.addWidget(widget, pos["row"], pos["col"], pos["row_span"], pos["col_span"])
                widget.setProperty("_grid_row", pos["row"])
                widget.setProperty("_grid_col", pos["col"])
                widget.setProperty("_row_span", pos["row_span"])
                widget.setProperty("_col_span", pos["col_span"])

    def toggle_edit_mode(self, enabled: bool) -> None:
        """
        Toggles layout customization mode, visually annotating cards with dashed outlines.
        Contract: WorkspaceLayoutManager.toggle_edit_mode(enabled: bool) -> None
        """
        self.is_edit_mode = enabled
        for name, widget in self.widgets_map.items():
            if not widget:
                continue
            widget.setProperty("editMode", "true" if enabled else "false")
            # Apply dynamic inline border for immediate visual feedback in edit mode
            if enabled:
                widget.setStyleSheet(widget.styleSheet() + "\nQFrame { border: 1px dashed #50535e; }")
            else:
                current_sheet = widget.styleSheet().replace("\nQFrame { border: 1px dashed #50535e; }", "")
                widget.setStyleSheet(current_sheet)
            widget.style().unpolish(widget)
            widget.style().polish(widget)
            widget.update()
