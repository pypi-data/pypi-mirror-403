"""
Copyright 2015 Computational Intelligence Research Laboratory, Chiang Mai, Thailand

Permission is hereby granted, free of charge, to any person obtaining a copy of this software 
and associated documentation files (the “Software”), to deal in the Software without restriction, 
including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, 
and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, 
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT 
NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. 
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, 
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE 
OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Please cited
Atcharin Klomsae, Sansanee Auephanwiriyakul, and Nipon Theera-Umpon, “A string grammar possibilistic-fuzzy C-medians”, 
Soft Computing , vol. 23, no. 17, pp. 7637 – 7653, 2019: http://doi.org/10.1007/s00500-018-3392-6.
"""

import multiprocessing
from typing import List, Optional
from functools import lru_cache
from typing import List, Tuple
import random, multiprocessing

# --------------------------- Levenshtein  ----------------------------
@lru_cache(maxsize=None)
def lev_cached(s1: str, s2: str) -> int:
    """
    Compute the Levenshtein distance between two strings (s1 and s2).
    @param s1: First input string.
    @param s2: Second input string.
    @return: The Levenshtein distance as an integer.

    Note:
    - The Levenshtein distance measures the minimum number of single edit operator 
    (insertions, deletions, or substitutions) required to transform one string into another.
    - This implementation uses dynamic programming and memorization via `functools.lru_cache` 
    to speed up repeated computations with the same string pairs.
    """
    len_s1, len_s2 = len(s1), len(s2)
    if len_s1 == 0: return len_s2
    if len_s2 == 0: return len_s1
    dp = [[0]*(len_s2+1) for _ in range(len_s1+1)]
    for i in range(len_s1+1): dp[i][0] = i
    for j in range(len_s2+1): dp[0][j] = j
    for i in range(1, len_s1+1):
        ai = s1[i-1]
        for j in range(1, len_s2+1):
            cost = 0 if ai == s2[j-1] else 1
            dp[i][j] = min(dp[i-1][j]+1, dp[i][j-1]+1, dp[i-1][j-1]+cost)
    return dp[len_s1][len_s2]

# ------------------------ weighted candidate score ----------------------
def candidate_score_weighted(args: Tuple[str, List[str], List[float]]):
    """
    Compute the weighted total distance score for a candidate string.
    @param args: A tuple containing:
        - cand: The candidate string to evaluate.
        - S: List of input strings representing the dataset.
        - W: List of weights corresponding to each string in S.
    @return: A tuple (cand, total) where total is the weighted sum of distances
    from cand to each string in S, weighted by W.
    """
    cand, S, W = args
    total = 0.0
    for w, x in zip(W, S):
        if w != 0.0:
            total += w * lev_cached(cand, x)
    return cand, total

# =============================== Base class ====================================
class BaseClustering:
    """
        Parameters
        ----------
        C: int
            Number of clusters.
        m: float
            Fuzziness parameter (>1.0).
        max_iter: int
            Maximum number of iterations.      
        tol: float
            Tolerance for convergence based on prototype position changes.
        refine_with_modified_median: bool
            Whether to refine prototypes using modified median.
        medoid_topK: int
            Number of top weighted strings to consider for medoid update.
        mm_jump_topK: int
            Number of top weighted strings to consider for modified median jumps.
        enforce_unique: bool
            Whether to enforce unique prototypes.
        min_proto_distance: int
            Minimum distance between prototypes if uniqueness is enforced.
        n_jobs: int or None
            Number of parallel jobs to use. Defaults to number of CPU cores.
        seed : int or None, default=48
            Random seed for reproducibility. If an integer is provided, the RNG
            will be deterministic with that seed. If None, random behavior is used.
        use_obj_stop: bool
            Whether to use objective function change for stopping criterion.
        obj_tol: float
            Tolerance for objective function change.
        
        Attributes
        ----------  
        prototypes_: List[str]
            Learned prototypes for clusters.
        alphabet_: str
            Alphabet of characters in the dataset.
    """
    def __init__(self, C=2, m=2.0, max_iter=100, tol=0.1,
                 refine_with_modified_median=True,
                 medoid_topK=400, mm_jump_topK=200,
                 enforce_unique=True, min_proto_distance=1,
                 n_jobs=None, seed=48,
                 use_obj_stop=True, obj_tol=1e-6):
        assert C >= 1 and m > 1.0
        self.C, self.m = int(C), float(m)
        self.max_iter, self.tol = int(max_iter), float(tol)
        self.refine_with_modified_median = bool(refine_with_modified_median)
        self.medoid_topK, self.mm_jump_topK = int(medoid_topK), int(mm_jump_topK)
        self.enforce_unique = bool(enforce_unique)
        self.min_proto_distance = int(min_proto_distance)
        self.n_jobs = n_jobs or multiprocessing.cpu_count()        
        self.use_obj_stop = bool(use_obj_stop)
        self.obj_tol = float(obj_tol)
        self.seed = seed
        if self.seed is not None:
            random.seed(seed)

        # learned state
        self.prototypes_: List[str] = []
        self.alphabet_: str = ""

    # ---- helpers ----
    def _d(self, a: str, b: str) -> int:
        """
        Compute the Levenshtein distance between two strings (a and b).
        @param a: First input string.
        @param b: Second input string.
        @return: The Levenshtein distance as an integer.
        """
        return lev_cached(a, b)
    
    def _cs(self, args: Tuple[str, List[str], List[float]]) -> Tuple[str, float]:
        """
        Compute the weighted total distance score for a candidate string.
        @param args: A tuple containing:
            - cand: The candidate string to evaluate.
            - S: List of input strings representing the dataset.
            - W: List of weights corresponding to each string in S.
            @return: A tuple (cand, total) where total is the weighted sum of distances
            from cand to each string in S, weighted by W.
        """
        return candidate_score_weighted(args)

    def _smart_init(self, S: List[str]) -> List[str]:
        """
        Smart initialization of prototypes using a farthest-first strategy.
        @param S: List of input strings representing the dataset.
        @return: List of initialized prototype strings.
        """
        seeds = [random.choice(S)] 
        while len(seeds) < min(self.C, len(S)):
            best_s, best_min = None, -1
            for s in S: 
                if s in seeds: 
                    continue 
                mind = min(self._d(s, t) for t in seeds) 
                if mind > best_min:
                    best_min, best_s = mind, s
            seeds.append(best_s if best_s is not None else random.choice([x for x in S if x not in seeds] or S))
        return seeds[:self.C]

    def _violates_hard_uniqueness(self, i: int, cand: str) -> bool:
        """
        Check whether a candidate prototype violates the hard uniqueness constraint.
        @param i: Index of the current prototype being evaluated.
        @param cand: Candidate prototype string.
        @return: True if the candidate violates uniqueness, False otherwise.
        """
        if not self.enforce_unique: return False 
        delta = self.min_proto_distance
        for j, pj in enumerate(self.prototypes_):
            if pj is None or j == i: continue
            if cand == pj: return True 
            if delta > 0 and self._d(cand, pj) < delta: return True
        return False

    def _update_prototype_medoid(self, i: int, S: List[str], W: List[float],
                                 mp_pool) -> str: 
        """
        find the medoid prototype for cluster i based on weighted distances.
        @param i: Index of the current prototype being updated.
        @param S: List of input strings representing the dataset.
        @param W: List of weights corresponding to each string in S.
        @param mp_pool: Multiprocessing pool for parallel computation.
        @return: medoid prototype string for cluster i.
        """
        N = len(S)
        K = min(self.medoid_topK, N)
        idx_by_w = sorted(range(N), key=lambda k: W[k], reverse=True)[:K]
        candidate_pool = [S[k] for k in idx_by_w if W[k] > 0] or S 

        args = [(cand, S, W) for cand in dict.fromkeys(candidate_pool)]
        results = mp_pool.map(candidate_score_weighted, args)

        scored = [(cand, base) for (cand, base) in results if not self._violates_hard_uniqueness(i, cand)]
        if not scored:
            scored = results
        scored.sort(key=lambda t: t[1])
        return scored[0][0]

    def _modified_median_refine(self, i: int, start: str, S: List[str], W_i: List[float],
                                mp_pool) -> str:
        """
        Refine the prototype for cluster i using the modified median approach.
        @param i: Index of the current prototype being refined.
        @param start: Starting prototype string.
        @param S: List of input strings representing the dataset.
        @param W_i: List of weights corresponding to each string in S for cluster i.
        @param mp_pool: Multiprocessing pool for parallel computation.
        @return: Refined prototype string for cluster i.
        """
        s = start
        alpha = "".join(sorted(set("".join(S))))
        alphabet = list(alpha)
        topK = min(self.mm_jump_topK, len(S))
        idx_by_w = sorted(range(len(S)), key=lambda k: W_i[k], reverse=True)[:topK]
        pool_strings = [S[k] for k in idx_by_w if W_i[k] > 0]

        pos = 0
        while pos < max(1, len(s)):
            candidates = [s]
            if len(s) > 0 and pos < len(s):
                for a in alphabet:
                    if a != s[pos]:
                        candidates.append(s[:pos] + a + s[pos+1:]) # substitution
                if len(s) > 1:
                    candidates.append(s[:pos] + s[pos+1:]) # deletion
            for a in alphabet:
                candidates.append(s[:pos] + a + s[pos:]) # insertion
            candidates.extend(pool_strings)
            candidates = list(dict.fromkeys(candidates))

            args = [(cand, S, W_i) for cand in candidates]
            results = mp_pool.map(candidate_score_weighted, args)

            scored = [(cand, base) for (cand, base) in results if not self._violates_hard_uniqueness(i, cand)]
            if not scored:
                scored = results
            scored.sort(key=lambda t: t[1])
            s = scored[0][0]
            pos += 1
        return s
    
    def predict(self, S: List[str], prototypes: List[str]) -> List[int]:
        """
        Predict cluster assignments for a list of strings based on current prototypes.
        @param S: List of input strings representing the dataset.
        @param prototypes: List of prototype strings for clusters.
        @return preds: List of predicted cluster indices for each string in S.
        """
        preds = []
        for s in S:
            distances = [lev_cached(s, proto) for proto in prototypes]
            preds.append(distances.index(min(distances)))
        return preds
    
# =====================================================================
# SGPFCMed — Possibilistic-Fuzzy 
# =====================================================================
class SGPFCMed(BaseClustering):
    """
    Hybrid clustering algorithm extending Possibilistic Fuzzy C-Means (PFCM) to string data, 
    using medoids as prototypes.

    Mathematical formulation:
    - Fuzzy membership (U): same as FCM
    - Typicality (T): T_ik = 1 / (1 + ((b * d_ik) / γ_i)^(1/(η - 1)))
    - γ_i = (Σ_k u_ik^m d_ik) / (Σ_k u_ik^m)
    - Objective function:
        J = Σ_k Σ_i (a * u_ik^m + b * t_ik^η) * d_ik + Σ_i γ_i Σ_k (1 - t_ik)^η
    This class extends BaseClustering and supports medoid-based prototype updates.
    """
    def __init__(self, C=2, m=2.0, eta=2.0, a=1.0, b=1.0, **kw):
        """
        Parameters:
        ----------
        C : int
            Number of clusters.
        m : float
            Fuzzifier exponent controlling fuzziness (for U).
        eta : float
            Exponent controlling typicality fuzziness (for T).
        a, b : float
            Balancing coefficients for fuzzy and possibilistic terms.
        """
        super().__init__(C, m, **kw)
        self.eta, self.a, self.b = float(eta), float(a), float(b)
        self.gamma_ = [1.0]*C
        self.U_: List[List[float]] = []; self.T_: List[List[float]] = []

    def fit(self, S: List[str]):
        """
        Train the SGPFCMed model on a list of strings using fuzzy-possibilistic C-medoids clustering.

        @param S: List of strings representing the dataset.
        @raises ValueError:
            - If input list S is empty.
            - If number of clusters C exceeds number of samples.

        @return self: Trained clustering model.

        Notes:
        ------
        - Uses both fuzzy membership (U) and typicality (T) to handle noise and outliers.
        - γ_i (gamma) is updated automatically each iteration.
        - Prototype update uses medoid selection + optional modified median refinement.
        - Distance computations are parallelized using multiprocessing.
        """
        if not S: raise ValueError("S must not be empty.")
        if self.C > len(S):
            raise ValueError(f"C={self.C} must not be greater than number of samples={len(S)}.")
        
        # Step 1: Initialize prototypes and matrices
        self.prototypes_ = self._smart_init(S)
        N = len(S)
        self.U_ = [[1.0/self.C]*self.C for _ in range(N)]
        self.T_ = [[0.5]*self.C for _ in range(N)]
        prev_J: Optional[float] = None

        with multiprocessing.Pool(self.n_jobs) as mp_pool:
            for _ in range(self.max_iter):
                old = self.prototypes_[:]
                tiny = 1e-12; expU = 1.0/(self.m-1.0); expT = 1.0/(self.eta-1.0)
                
                # Step 2: Update fuzzy membership matrix U
                U = []
                for k in range(N):
                    d = [float(self._d(S[k], p)) for p in self.prototypes_]
                    if min(d) <= tiny:
                        zero_idx = [i for i in range(self.C) if d[i] <= tiny]
                        zc = len(zero_idx)
                        row = [1.0/zc if i in zero_idx else 0.0 for i in range(self.C)]
                    else:
                        row = [1.0 / max(sum((d[i]/dj)**expU for dj in d), tiny) for i in range(self.C)]
                        ssum = sum(row); row = [u/ssum for u in row]
                    U.append(row)
                self.U_ = U
                
                # Step 3: Update typicality matrix T using γ_i
                T = [[0.0]*self.C for _ in range(N)]
                for k in range(N):
                    for i in range(self.C):
                        d = float(self._d(S[k], self.prototypes_[i]))
                        T[k][i] = 1.0 if d<=tiny else 1.0/(1.0 + ((self.b*d)/max(self.gamma_[i],tiny))**expT)
                self.T_ = T
                
                # Step 4: Update γ_i (scale parameter) based on U
                newg = []
                for i in range(self.C):
                    num = den = 0.0
                    for k in range(N):
                        w = (self.U_[k][i] ** self.m)
                        num += w * self._d(S[k], self.prototypes_[i]); den += w
                    newg.append(num/den if den>0 else 1.0)
                self.gamma_ = newg
                
                # Step 5: Update prototypes
                for i in range(self.C):
                    W_i = [self.a*(self.U_[k][i]**self.m) + self.b*(self.T_[k][i]**self.eta) for k in range(N)]
                    med = self._update_prototype_medoid(i, S, W_i, mp_pool)
                    self.prototypes_[i] = self._modified_median_refine(i, med, S, W_i, mp_pool) \
                        if self.refine_with_modified_median else med
                
                # Step 6: Check for convergence
                by_pos = max(self._d(old[i], self.prototypes_[i]) for i in range(self.C))
                J = self.objective(S)
                if self.use_obj_stop and prev_J is not None:
                    rel = abs(prev_J - J) / max(1.0, prev_J)
                    if rel < self.obj_tol: break
                prev_J = J
                if by_pos < self.tol and not self.use_obj_stop: break
        return self

    def objective(self, S: List[str]) -> float:
        """
        Compute the objective function J of the SGPFCMed model.

        @param S: List of strings (dataset).
        @return J: Objective function value.

        Formula:
        J = Σ_k Σ_i (a * u_ik^m + b * t_ik^η) * d_ik + Σ_i γ_i Σ_k (1 - t_ik)^η
        """
        J = 0.0
        # Distance-based fuzzy + possibilistic terms
        for k, x in enumerate(S):
            for i, p in enumerate(self.prototypes_):
                J += (self.a*(self.U_[k][i]**self.m) + self.b*(self.T_[k][i]**self.eta)) * self._d(x, p)
         # Typicality regularization
        for i in range(self.C):
            for k in range(len(S)):
                J += self.gamma_[i] * ((1.0 - self.T_[k][i]) ** self.eta)
        return J
    
    def membership(self) -> List[List[float]]:
        """
        @return U_: The current fuzzy membership matrix.
        """
        return self.U_
    
    def prototypes(self) -> List[str]:
        """
        @return prototypes_: The current list of cluster prototypes.
        """
        return self.prototypes_

    def typicality(self) -> List[List[float]]:
        """
        @return T_: The current typicality matrix.
        """
        return self.T_
