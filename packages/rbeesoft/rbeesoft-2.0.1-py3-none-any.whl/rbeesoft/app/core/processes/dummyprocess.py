import time
from rbeesoft.app.core.processes.process import Process


class DummyProcess(Process):
    def __init__(self):
        super(DummyProcess, self).__init__()
        self._n = 10

    def execute(self):
        out = []
        for i in range(self._n):
            if self.is_canceled():
                return out
            time.sleep(0.25)
            out.append(i)
            self.progress.emit(int((i+1)/self._n*100))
        return out
