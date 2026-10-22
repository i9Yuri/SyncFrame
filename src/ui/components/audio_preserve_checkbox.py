"""High-contrast checkbox for original secondary audio preservation with dynamic text state."""

from typing import Optional
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QCheckBox, QWidget


class AudioPreserveCheckbox(QCheckBox):
    """
    High-contrast audio preservation selector with dynamic, explicit textual feedback:
    - Checked: 'Preservar áudio original em inglês: Sim (Faixa Secundária)'
      Displays high-contrast solid emerald indicator with crisp checkmark.
    - Unchecked: 'Preservar áudio original em inglês: Não'
      Displays hollow/subtle dark indicator with clear off-state styling.
    """
    state_description_changed = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None, language_name: str = "inglês"):
        super().__init__(parent)
        self.setObjectName("audioPreserveToggle")
        self.setProperty("class", "highContrastToggle")
        self.setCursor(Qt.PointingHandCursor)

        self._language_name = language_name
        self.setChecked(True)
        self._update_label(True)

        self.toggled.connect(self._on_toggled)

    @property
    def language_name(self) -> str:
        return self._language_name

    def set_language_name(self, lang_name: str):
        self._language_name = lang_name if lang_name else "inglês"
        self._update_label(self.isChecked())

    def _on_toggled(self, checked: bool):
        desc = self._update_label(checked)
        self.state_description_changed.emit(desc)

    def _update_label(self, checked: bool) -> str:
        if checked:
            text = f"Preservar áudio original em {self._language_name}: Sim (Faixa Secundária)"
        else:
            text = f"Preservar áudio original em {self._language_name}: Não"
        self.setText(text)
        return text
