import pickle

class Benchmark (object):
    def save(self, path=None, verbose=False):
        f = path if path else self.file_name + ".save"
        if verbose:
            print("Saving results to:", self.file_name + ".save")
        with open(f, "wb") as f:
            pickle.dump(self.results, f)

    def load(self, path=None, verbose=False):
        f = path if path else self.file_name + ".save"
        if verbose:
            print("Loading results from:", self.file_name + ".save")
        with open(f, "rb") as f:
            self.results = pickle.load(f)

