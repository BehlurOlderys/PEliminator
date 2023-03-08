from package.processes.remote_process import RemoteProcessGUI
from multiprocessing import Event


if __name__ == "__main__":
    kill_event = Event()
    gui = RemoteProcessGUI(kill_event=kill_event)
    gui.run()
