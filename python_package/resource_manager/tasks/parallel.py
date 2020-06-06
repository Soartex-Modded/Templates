from multiprocessing import Queue, Process, cpu_count
import time


def parallelize(items, function, args=None):
    """
    General function for exhausting a queue of items over multiple processes
    :param items: the queue, each item is the first argument to function
    :param function: function to map over all items in queue
    :param args: additional arguments for the function
    """

    def process_wrapper(item_queue, function, arguments):
        while not item_queue.empty():
            item = item_queue.get()

            if arguments is None:
                function(item)
            else:
                function(item, *arguments)

    file_queue = Queue()

    for item in items:
        file_queue.put(item)

    pool = [Process(target=process_wrapper, args=(file_queue, function, args), name=str(proc))
            for proc in range(cpu_count())]

    for proc in pool:
        proc.start()

    while any([proc.is_alive() for proc in pool]):
        time.sleep(1)

    for proc in pool:
        proc.terminate()
