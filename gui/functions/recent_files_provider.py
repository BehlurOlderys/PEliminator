from tkinter import filedialog
import os
from threading import Thread, Event

waiting_event = Event()


def is_file_wanted(f, extensions):
    """
    extensions is an array of wanted file extensions
    """
    is_any = any([f.lower().endswith(e) for e in extensions])
    return is_any


def is_file_fits(f):
    return is_file_wanted(f, ["fit", "fits"])


def is_file_png(f):
    return is_file_wanted(f, ["png"])


def get_last_files(d, filter_fun):
    """
    returns list of pairs (file, timestamp) sorted by timestamp
    """
    files = [os.path.join(d, f) for f in os.listdir(d) if filter_fun(f)]
    files = [(p, os.path.getctime(p)) for p in files]
    return sorted(files, key=lambda x: x[1])



class RecentImagesProvider:
    def __init__(self, processor, filter_fun):
        self._processor = processor
        self._filter_fun = filter_fun
        self._files = []
        self._kill = False
        self._thread = None
        self._filenames = None
        self._main_dir = None

    def start(self, directory=None):
        print("Starting provider...")

        if directory is not None:
            self._main_dir = directory
        self._thread = Thread(target=self._run)
        self._thread.start()

    def _run(self):
        if self._main_dir is None:
            print("No main dir given, choosing new...")
            self._main_dir = filedialog.askdirectory(title="Open dir with images for provider")
        if not self._main_dir:
            print("Direction with images failed to open, returning...")
            return
        print(f"Using directory: {self._main_dir}")
        while not self._files:
            self._files = get_last_files(self._main_dir, self._filter_fun)
            if not self._files:
                print("Waiting 1s for new files...")
                waiting_event.wait(1)
        self._filenames = [os.path.basename(f[0]) for f in self._files]
        f, t = self._files[-1]
        if not self._processor.init(f, t):
            print("Initialization failed, ending...")
            return
        print(f"Initializing with file = {f}")

        self._process()

    def kill(self):
        self._kill = True
        if self._thread is not None and self._thread.ident is not None:
            print("RFP (kill):Joining thread!")
            self._thread.join()
        else:
            print("RFP (kill): Nothing to join!")

    def __del__(self):
        if not self._kill:
            self._kill = True
        if self._thread is not None and self._thread.ident is not None:
            print("RFP (del):Joining thread!")
            self._thread.join()
        else:
            print("RFP (del): Nothing to join!")

    def _process(self):
        while not self._kill:
            latest_state = get_last_files(self._main_dir, self._filter_fun)
            latest_filenames = [os.path.basename(f) for f, t in latest_state]
            new_files = [f for f in latest_state if os.path.basename(f[0]) not in self._filenames]
            new_filenames = [os.path.basename(f) for f, t in new_files]

            if not new_files:
                print("Waiting 0.1s for new files...")
                self._processor.idle()
                waiting_event.wait(0.25)
                continue

            print(f"Acquired  {len(new_files)} new files")
            for f, t in new_files:
                print(f"Processing file {f}")
                self._processor.process(f, t)

            self._filenames += new_filenames


class TestProcessor:
    def __init__(self):
        pass

    def init(self, f, t):
        print(f"Initializing test processor with file {f}")

    def process(self, f, t):
        print(f"Processing file {f}")


# przykładowe użycie:
# t = TestProcessor()
# r = RecentImagesProvider(t, is_file_png)
# r.start()
#(...) cokolwiek innego
#r.kill()