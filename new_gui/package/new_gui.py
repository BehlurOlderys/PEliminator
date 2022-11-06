from multiprocessing import Process, Queue
from processes.test_add_process1 import TestAddingGui1
from processes.test_add_process2 import TestAddingGui2


def printer(in_queue):
    gui = TestAddingGui2(in_queue=in_queue)
    gui.run()


if __name__ == '__main__':
    q = Queue()
    p = Process(target=printer, args=(q,))
    p.start()

    test1 = TestAddingGui1(q)
    test1.run()
    q.put('KILL_ME_PLEASE')
    p.join()
