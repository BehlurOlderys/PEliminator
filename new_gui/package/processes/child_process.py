from package.widgets.application import SimpleGuiApplication


check_if_parent_alive_timeout_ms = 1000


class ChildProcessGUI(SimpleGuiApplication):
    def __init__(self, kill_event, *args, **kwargs):
        super(ChildProcessGUI, self).__init__(*args, **kwargs)
        self._kill_event = kill_event
        self._root.protocol('WM_DELETE_WINDOW', self._killme)

    def _check_if_parent_alive(self):
        if self._kill_event.is_set():
            self._root.destroy()
        self._root.after(check_if_parent_alive_timeout_ms, self._check_if_parent_alive)

    def run(self):
        self._root.after(check_if_parent_alive_timeout_ms, self._check_if_parent_alive)
        super(ChildProcessGUI, self).run()

    def _killme(self):
        self._kill_event.set()
        self._root.destroy()
