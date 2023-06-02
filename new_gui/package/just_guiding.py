from package.processes.advanced_guiding_process import AdvancedGuidingProcess
from multiprocessing import Event


if __name__ == "__main__":
    kill_event = Event()
    gui = AdvancedGuidingProcess(kill_event=kill_event)
    gui.run()
