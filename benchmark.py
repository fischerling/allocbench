import pickle

class Benchmark (object):
    def save(self, verbose=False):
        if verbose:
            print("Saving results to:", self.file_name + ".save")
        with open(self.file_name + ".save", "wb") as f:
            pickle.dump(self.results, f)

    def load(self, verbose=False):
        if verbose:
            print("Loading results from:", self.file_name + ".save")
        with open(self.file_name + ".save", "rb") as f:
            self.results = pickle.load(f)

