from multiprocessing import Process, Queue
from processes.guiding_process import GuidingProcessGUI


def guider(serial_queue):
    gui = GuidingProcessGUI(out_queue=serial_queue)
    gui.run()


if __name__ == '__main__':
    serial_write_queue = Queue()
    p = Process(target=guider, args=(serial_write_queue,))
    p.start()
    # serial_write_queue.put('KILL_ME_PLEASE')
    p.join()
