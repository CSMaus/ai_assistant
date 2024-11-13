from queue import Queue
from threading import Thread
from command_process import execute_command

command_queue = Queue()


def command_listener():
    while True:
        command, args = command_queue.get()
        execute_command(command, *args)
        command_queue.task_done()


if __name__ == "__main__":
    listener_thread = Thread(target=command_listener)
    listener_thread.daemon = True
    listener_thread.start()

    listener_thread.join()

