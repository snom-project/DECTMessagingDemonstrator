#!python3
#coding=utf-8
""" https://stackoverflow.com/q/49081260/ """

import sys, time, threading, queue

print(sys.version)

class myClass:
    """ """

    def __init__(self):
        """ """
        self.q = queue.Queue()
        self.threads = []
        self.num_worker_threads = 3

        print("starting thread(s)")
        for i in range(self.num_worker_threads):
            t = threading.Thread(target=self.backgroundFunc)
            t.start()
            self.threads.append(t)

        print("giving thread(s) some work")
        for item in range(5):
            self.q.put(item)

        print("giving thread(s) more work")
        for item in range(5,10):
            self.q.put(item)

        # block until all tasks are done
        print("waiting for thread(s) to finish")
        self.q.join()

        # stop workers
        print("stopping thread(s)")
        #for i in range(self.num_worker_threads):
        #    self.q.put(None)
        for t in self.threads:
            self.q.join()

        print("finished")


    def backgroundFunc(self):
        """ """
        print("thread started")
        #while True:
        item = self.q.get()
        if item is None:
            self.q.task_done()
            #break
        print("working on ", item)
        time.sleep(0.5)
        self.q.task_done()
        print("thread stopping")

    def mainFunc(self):
        """ """

        print("starting thread(s)")
        for i in range(self.num_worker_threads):
            t = threading.Thread(target=self.backgroundFunc)
            t.start()
            self.threads.append(t)

        print("giving thread(s) some work")
        for item in range(5):
            self.q.put(item)

        print("giving thread(s) more work")
        for item in range(5,10):
            self.q.put(item)

        # block until all tasks are done
        print("waiting for thread(s) to finish")
        #self.q.join()

        # stop workers
        print("stopping thread(s)")
        #for i in range(self.num_worker_threads):
        #    self.q.put(None)
        #for t in self.threads:
        #    self.q.join()

        print("finished")


if __name__ == "__main__":
    print("instance")
    myClassInstance = myClass()

    print("run")
    #myClassInstance.mainFunc()

    print("end.")