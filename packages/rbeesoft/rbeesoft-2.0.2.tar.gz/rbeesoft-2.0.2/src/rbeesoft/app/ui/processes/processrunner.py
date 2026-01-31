from rbeesoft.common.singleton import singleton
from rbeesoft.common.logmanager import LogManager

LOG = LogManager()


@singleton
class ProcessRunner:
    current_process = {}

    def start(self, process, callback_progress=None, callback_finished=None, callback_failed=None):
        if callback_progress:
            process.progress.connect(callback_progress)
        else:
            process.progress.connect(self.handle_process_progress)
        if callback_finished:
            process.finished.connect(callback_finished)
        else:
            process.finished.connect(self.handle_process_finished)
        if callback_failed:
            process.failed.connect(callback_failed)
        else:
            process.failed.connect(self.handle_process_failed)
        self.current_process = process
        self.current_process.start()

    def handle_process_progress(self, progress):
        LOG.info(f'Progress: {progress}')

    def handle_process_finished(self, result):
        LOG.info(f'Process finished successfully: {result}')

    def handle_process_failed(self, error):
        LOG.error(f'Process failed ({error})')