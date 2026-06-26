import keyboard


class GlobalHotkeyService:
    def __init__(self, keyboard_module=None):
        self.keyboard_module = keyboard_module or keyboard
        self._hotkeys = []

    def register(self, hotkey: str, callback) -> None:
        hotkey_id = self.keyboard_module.add_hotkey(hotkey, callback)
        self._hotkeys.append(hotkey_id)

    def unregister_all(self) -> None:
        for hotkey_id in self._hotkeys:
            self.keyboard_module.remove_hotkey(hotkey_id)
        self._hotkeys = []
