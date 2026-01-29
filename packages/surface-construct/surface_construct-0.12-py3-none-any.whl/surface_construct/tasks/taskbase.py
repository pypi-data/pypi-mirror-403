import pickle

from ase.utils import IOContext
from ase.parallel import world


class TaskBase(IOContext):
    pkl_content = []
    def __init__(self, comm=world, **kwargs):
        self.kwargs = kwargs or dict()
        self.hist_pkl = self.kwargs.get('hist_pkl', 'task_hist.pkl')
        self.atoms = None  # 临时的结构
        logfile = kwargs.get('logfile', self.__class__.__name__.lower()+'.log')
        self.logfile = self.openfile(logfile, comm=comm, mode='a')

    def print_task_info(self):
        msg = [f"Starting task {self.__class__.__name__}"]
        msg += [f"{k}  :  {v}" for k,v in self.kwargs.items()]
        self.log("\n".join(msg))

    def to_pkl(self):
        content = dict()
        for c in self.pkl_content:
            content[c] = getattr(self, c)
        file_pi = open(self.hist_pkl, 'wb')
        pickle.dump(content, file_pi)
        file_pi.close()

    def from_pkl(self):
        msg = [f"\nContinue sampling from pickle file {self.hist_pkl}"]
        file_pi = open(self.hist_pkl, 'rb')
        content = pickle.load(file_pi)
        file_pi.close()
        for c in self.pkl_content:
            setattr(self, c, content[c])
            msg.append(f"Reading information of {c} from pickle.")
        self.log("\n".join(msg))

    def run(self):
        self.print_task_info()

    def log(self, msg):
        self.logfile.write(msg)
        self.logfile.flush()
