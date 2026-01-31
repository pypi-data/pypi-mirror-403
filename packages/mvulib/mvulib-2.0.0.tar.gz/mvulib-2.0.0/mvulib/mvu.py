import mvulib
import matlab
import numpy as np
import time
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import pairwise_distances

class Mvu:
    def __init__(self, n_neighbors=5, angles=2, slack=True, gamma=2.5e+01,\
                 eps=1e-08, bigeps=1e-05, maxiter=150, mode="data", verbose=True):
        
        self.n_neighbors=n_neighbors
        self.angles=angles
        self.slack=slack
        self.gamma=gamma
        self.eps=eps
        self.bigeps=bigeps
        self.maxiter=maxiter
        self.mode=mode
        self.verbose=verbose
        self.n_samples=None
        self.n_features=None
        self.adjacency_matrix=None
        self.K=None
        self.S=None
        self.cost=None
        self.eigenvalues=None
        self._Y=None
        self.n_components=None
        self.embedding=None
        self.reconstruction_error=None
        self.reconstruction_error_rel=None
        self.n_constraints=None
        self.iter=None
        self.feasratio=None
        self.numerr=None
        self.pinf=None
        self.dinf=None
        self.CONST=None
        
    def fit(self, X):
        
        if self.verbose:
            print(f"{'='*32} MVU {'='*32}\n")
            
        start=time.time()

        n=X.shape[0]
        self.n_samples=n
        
        if self.mode=="data":
            DD=pairwise_distances(X)**2
            self.n_features=X.shape[1]
        elif self.mode=="distance":
            DD=X
            self.n_features=None
        else:
            raise Exception(f"Unknown data mode {self.mode}! Valid options are 'data' and 'distance'.")

        if self.angles!=0 and self.angles!=1 and self.angles!=2:
            raise Exception(f"Invalid value of angles parameter! Allowed values are 0, 1 and 2.")

        if self.verbose:
            print(f"Parameters:\n"+\
                  f"n_samples={self.n_samples}\n"
                  f"n_features={self.n_features}\n"+\
                  f"n_neighbors={self.n_neighbors}\n"
                  f"angles={self.angles}\n"+\
                  f"slack={self.slack}\n"+\
                  f"gamma={self.gamma}\n"+\
                  f"eps={self.eps}\n"+\
                  f"bigeps={self.bigeps}\n"+
                  f"maxiter={self.maxiter}\n")
        
        DD=np.ascontiguousarray(DD.astype(np.float64))
        DDIn=matlab.double(DD, size=DD.shape)
        kIn=matlab.double(np.array([self.n_neighbors]).astype(np.float64), size=(1,1))
        anglesStrIn="angles"
        anglesIn=matlab.double(np.array([self.angles]).astype(np.float64), size=(1,1))
        slackStrIn="slack"
        slackIn=matlab.double(np.array([1 if self.slack else 0]).astype(np.float64), size=(1,1))
        gammaStrIn="gamma"
        gammaIn=matlab.double(np.array([self.gamma]).astype(np.float64), size=(1,1))
        epsStrIn="eps"
        epsIn=matlab.double(np.array([self.eps]).astype(np.float64), size=(1,1))
        bigepsStrIn="bigeps"
        bigepsIn=matlab.double(np.array([self.bigeps]).astype(np.float64), size=(1,1))
        maxIterStrIn="maxiter"
        maxIterIn=matlab.double(np.array([self.maxiter]).astype(np.float64), size=(1,1))

        if self.verbose:
            print("Solving problem...\n")
            
        lib=mvulib.initialize()
        YOut, detailsOut=lib.mvu(DDIn, kIn, anglesStrIn, anglesIn, slackStrIn, slackIn, gammaStrIn, gammaIn, epsStrIn, epsIn, bigepsStrIn, bigepsIn, maxIterStrIn, maxIterIn,  nargout=2)
        lib.terminate()
        
        self._Y=np.array(YOut)
        rows=np.array(detailsOut["rAdj"]).flatten()-1
        cols=np.array(detailsOut["cAdj"]).flatten()-1
        self.adjacency_matrix=csr_matrix((np.repeat(1, len(rows)), (rows, cols)), shape=(n, n), dtype="int")
        self.K=np.array(detailsOut["K"])
        if self.slack:
            self.S=np.array(detailsOut["S"])
        self.cost=detailsOut["cost"]
        self.eigenvalues=np.array(detailsOut["eigvals"]).flatten()
        self.n_constraints=int(detailsOut["nconstr"])
        self.iter=int(detailsOut["iter"])
        self.feasratio=detailsOut["feasratio"]
        self.numerr=int(detailsOut["numerr"])
        self.pinf=int(detailsOut["pinf"])
        self.dinf=int(detailsOut["dinf"])
        self.CONST=detailsOut["CONST"]

        self.n_components=None
        self.embedding=None
        self.reconstruction_error=None
        self.reconstruction_error_rel=None

        finish=time.time()
        time_taken=round(finish-start, 2)

        if self.verbose:
            print(f"Solver exit status:\n"+\
                  f"numerr={self.numerr}\n"+\
                  f"feasratio={self.feasratio}\n"+\
                  f"pinf={self.pinf}\n"+\
                  f"dinf={self.dinf}\n")
            print(f"Execution took {time_taken} seconds.\n")
            print(f"{'='*69}\n")
        return self

    def transform(self, p):
        if self._Y is None:
            raise Exception("Call Mvu.fit prior to calling transform!")
        self.embedding=self._Y[:, 0:p]
        self.n_components=p
        cost_kmds=np.sum(self.eigenvalues[p:]**2)
        self.reconstruction_error=np.sqrt(cost_kmds)
        self.reconstruction_error_rel=self.reconstruction_error/np.sqrt(cost_kmds+np.sum(self.eigenvalues[:p]**2))
        return self.embedding

    def fit_transform(self, X, p):
        return self.fit(X).transform(p)

    def summarize(self):
        print(f"Solver Summary:\n"+\
              f"n_constr={self.n_constraints}\n"+\
              f"iter={self.iter}\n"+\
              f"numerr={self.numerr}\n"+\
              f"feasratio={self.feasratio}\n"+\
              f"pinf={self.pinf}\n"+\
              f"dinf={self.dinf}\n")
        print(f"Mvu Summary:\n"+\
              f"cost={self.cost}\n"+\
              f"n_components={self.n_components}\n"+\
              f"reconstruction_error={self.reconstruction_error}\n"+\
              f"reconstruction_error_rel={self.reconstruction_error_rel}")

    def __str__(self):
        return f"n_neighbors={self.n_neighbors}, angles={self.angles}, slack={self.slack}, gamma={self.gamma}, eps={self.eps}, bigeps={self.bigeps}, maxiter={self.maxiter}"
