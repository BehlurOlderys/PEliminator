from multiprocessing import Process, Queue
from processes.main_gui import MainGui


def main_gui(serial_write_q, serial_read_q):
    gui = MainGui(serial_out_queue=serial_write_q, serial_in_queue=serial_read_q)
    gui.run()


if __name__ == '__main__':
    serial_write_queue = Queue()
    serial_read_queue = Queue()
    p = Process(target=main_gui, args=(serial_write_queue, serial_read_queue, ))
    p.start()
    # serial_write_queue.put('KILL_ME_PLEASE')
    p.join()
