import time
from tkinter import filedialog
import os
from time import sleep
from threading import Thread


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

    def start(self):
        self._thread = Thread(target=self._run)
        self._thread.start()

    def _run(self):
        self._main_dir = filedialog.askdirectory(title="Open dir with images")
        while not self._files:
            self._files = get_last_files(self._main_dir, self._filter_fun)
            if not self._files:
                print("Waiting 1s for new files...")
                sleep(1)
        self._filenames = [f[0] for f in self._files]
        if not self._processor.init(*self._files[-1]):
            print("Initialization failed, ending...")
            return

        self._process()

    def kill(self):
        self._kill = True
        self._thread.join()

    def __del__(self):
        if not self._kill:
            self._kill = True
            self._thread.join()

    def _process(self):
        while not self._kill:
            files = get_last_files(self._main_dir, self._filter_fun)
            new_files = [f for f in files if f[0] not in self._filenames]

            if not new_files:
                print("Waiting 1s for new files...")
                sleep(1)
                continue

            print(f"Acquired  {len(new_files)} new files")
            for f, t in new_files:
                self._processor.process(f, t)

            self._files += new_files
            self._filenames = [f[0] for f in files]


class TestProcessor:
    def __init__(self):
        pass

    def init(self, f, t):
        print(f"Initializing test processor with file {f}")

    def process(self, f, t):
        print(f"Processing file {f}")


# przykładowe użycie:
t = TestProcessor()
r = RecentImagesProvider(t, is_file_png)
r.start()
#(...) cokolwiek innego
#r.kill()