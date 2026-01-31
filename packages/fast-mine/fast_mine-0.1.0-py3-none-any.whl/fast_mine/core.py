
import numpy as np
from numba import jit, prange
from dataclasses import dataclass
from typing import Tuple, Optional, List

# Constants
EST_MIC_APPROX = 0
EST_MIC_E = 1

@dataclass
class MineParameter:
    alpha: float = 0.6
    c: float = 15.0
    est: int = EST_MIC_APPROX

@dataclass
class MineScore:
    n: int
    m: np.ndarray
    M: List[np.ndarray]

@dataclass
class MineProblem:
    x: np.ndarray
    y: np.ndarray
    n: int
    
# --- Core Logic with Numba ---

@jit(nopython=True, cache=True)
def equipartition_y_axis(dy, n, y):
    Q_map = np.zeros(n, dtype=np.int32)
    rowsize = float(n) / float(y)
    
    i = 0
    h = 0
    curr = 0
    
    while i < n:
        start = i
        val = dy[i]
        while i < n and dy[i] == val:
            i += 1
        s = i - start
        
        temp1 = abs(float(h + s) - rowsize)
        temp2 = abs(float(h) - rowsize)
        
        if (h != 0) and (temp1 >= temp2):
            curr += 1
            h = 0
            temp1 = float(n - start)
            temp2 = float(y - curr)
            if temp2 != 0:
                rowsize = temp1 / temp2
                
        Q_map[start:i] = curr
        h += s
        
    return Q_map, curr + 1

@jit(nopython=True, cache=True)
def get_clumps_partition(dx, n, Q_map):
    Q_tilde = Q_map.copy()
    i = 0
    c = -1
    
    while i < n:
        start = i
        val = dx[i]
        flag = False
        
        while i < n and dx[i] == val:
            if Q_tilde[start] != Q_tilde[i]:
                flag = True
            i += 1
        s = i - start
            
        if (s > 1) and flag:
            Q_tilde[start:i] = c
            c -= 1
        
    P_map = np.zeros(n, dtype=np.int32)
    
    if n > 0:
        current_p = 0
        for k in range(1, n):
            if Q_tilde[k] != Q_tilde[k-1]:
                current_p += 1
            P_map[k] = current_p
        p = current_p + 1
    else:
        p = 0
        
    return P_map, p

@jit(nopython=True, cache=True)
def get_superclumps_partition(dx, n, k_hat, Q_map):
    P_map, p = get_clumps_partition(dx, n, Q_map)
    if p > k_hat:
        dp = P_map.astype(np.float64)
        P_map, p = equipartition_y_axis(dp, n, k_hat)
    return P_map, p

@jit(nopython=True, cache=True)
def optimize_x_axis_core(c, c_log, cumhist, cumhist_log, q, p, n, x_sz):
    # Base H(Q)
    total_log = np.log(n)
    c_last = cumhist[:, p-1]
    mask = c_last > 0
    
    # H(Q) calculation
    term = np.zeros(q)
    for i in range(q):
        if mask[i]:
            prob = c_last[i] / n
            term[i] = prob * (cumhist_log[i, p-1] - total_log)
    HQ = -np.sum(term)
    
    score_vec = np.zeros(x_sz - 1) 

    # M Matrix for DP: M[k, t]
    # k: number of bins (1..x_sz) (implemented as 0..x_sz index for safe access)
    # t: ending partition index (0..p-1)
    
    # We will implement logic similar to the C code's Algorithm 2.
    # C code computes I[t][l] which is "Master" Maximum Mutual Information using l partitions ending at t.
    # Here we are computing MI directly.
    
    # C code's logic:
    # 1. Compute HQ
    # 2. Optimal partitions of size 2 (I[t][2]) = max_s (HQ + F(s, t))
    # 3. Inductive (I[t][l])
    
    # Let's reproduce C code logic structure exactly for correctness with Numba, 
    # as the previous suggested 'E' matrix approach simplifies but might deviate from C implementation details regarding F(s,t).
    
    # Pre-computations:
    # HP2Q[s, t] for s,t in 0..p
    # Using float64
    HP2Q = np.zeros((p + 1, p + 1))
    
    # Note on indices: Numba uses 0-based. C used 1-based logic (s=1..p).
    # We will map C's s (1-based) to Python s-1.
    # C loops: t=3..p, s=2..t.
    # Python indices: t_idx=2..p-1, s_idx=1..t_idx.
    
    # Implementing hp2q logic inline or helper
    # hp2q(cumhist, c, q, p, s, t)
    # s, t are 1-based in C. s < t.
    
    for t_c in range(3, p + 1):
        t = t_c - 1
        for s_c in range(2, t_c + 1):
            s = s_c - 1
            
            # HP2Q calculation
            total_count = float(c[t] - c[s])
            if total_count <= 0:
                HP2Q[s_c, t_c] = 0.0
                continue
                
            total_term_log = np.log(total_count)
            val = 0.0
            
            for y_bin in range(q):
                diff = cumhist[y_bin, t] - cumhist[y_bin, s]
                if diff > 0:
                    prob = diff / total_count
                    val += prob * (np.log(float(diff)) - total_term_log)
            
            HP2Q[s_c, t_c] = -val

    # F Matrix? No, compute on fly or store needed parts.
    
    # I Matrix: (p+1) x (x_sz+1). 
    I = np.zeros((p + 1, x_sz + 1))
    
    # t=2..p (C logic) -> t_c in 2..p
    # s=1..t -> s_c in 1..t_c
    
    # Find optimal partitions of size 2
    for t_c in range(2, p + 1):
        t = t_c - 1
        f_max = -np.inf
        
        for s_c in range(1, t_c + 1):
            s = s_c - 1
            
            # Compute F(s, t) for size 2
            # F = hp3(s, t) - hp3q(s, t)
            
            # hp3(s, t)
            # s_c, t_c match C params
            
            if s_c == t_c:
                hp3_val = 0.0
            else:
                total_hp3 = c[t]
                total_hp3_log = np.log(float(total_hp3))
                hp3_val = 0.0
                
                # Part 1: [0, s]
                cnt_s = c[s]
                if cnt_s > 0:
                    prob = cnt_s / total_hp3
                    # c_log passed in? Or computed?
                    # c_log is usually valid where c>0
                    # prob_log = c_log[s] - total_hp3_log
                    hp3_val -= prob * (np.log(float(cnt_s)) - total_hp3_log)
                
                # Part 2: [s, t]
                cnt_diff = c[t] - c[s]
                if cnt_diff > 0:
                    prob = cnt_diff / total_hp3
                    hp3_val -= prob * (np.log(float(cnt_diff)) - total_hp3_log)
            
            # hp3q(s, t)
            hp3q_val = 0.0
            total_hp3q = c[t]
            total_hp3q_log = np.log(float(total_hp3q))
            
            for y_bin in range(q):
                # part 1
                cnt_is = cumhist[y_bin, s]
                if cnt_is > 0:
                    prob = cnt_is / total_hp3q
                    hp3q_val -= prob * (cumhist_log[y_bin, s] - total_hp3q_log)
                
                # part 2
                cnt_it = cumhist[y_bin, t]
                cnt_diff = cnt_it - cnt_is
                if cnt_diff > 0:
                    prob = cnt_diff / total_hp3q
                    hp3q_val -= prob * (np.log(float(cnt_diff)) - total_hp3q_log)
            
            F = hp3_val - hp3q_val
            if F > f_max:
                f_max = F
                
        I[t_c, 2] = HQ + f_max
            
    # Inductive Step
    # l=3..x_sz
    for l in range(3, x_sz + 1):
        for t_c in range(l, p + 1):
            t = t_c - 1
            ct = float(c[t])
            if ct == 0: continue
            
            f_max = -np.inf
            
            # s=l-1..t
            for s_c in range(l - 1, t_c + 1):
                s = s_c - 1
                cs = float(c[s])
                
                # F calculation
                # F = (cs/ct)*(I[s][l-1]-HQ) - ((ct-cs)/ct)*HP2Q[s][t]
                
                term1 = (cs / ct) * (I[s_c, l-1] - HQ)
                term2 = ((ct - cs) / ct) * HP2Q[s_c, t_c]
                
                F = term1 - term2
                
                if F > f_max:
                    f_max = F
            
            I[t_c, l] = HQ + f_max
            
    # Fill rest (if p < x_sz)
    # C code: for (i=p+1; i<=x; i++) I[p][i] = I[p][p];
    if p < x_sz:
         last_val = I[p, p]
         for k in range(p + 1, x_sz + 1):
             I[p, k] = last_val
             
    # Result
    # score[i-2] = I[p][i] / min(...)
    for k in range(2, x_sz + 1):
        numer = I[p, k]
        denom = min(np.log(k), np.log(q))
        if denom > 0:
            score_vec[k-2] = numer / denom
        else:
            score_vec[k-2] = 0.0
            
    return score_vec

@jit(nopython=True, cache=True)
def optimize_x_axis(dx, dy, n, Q_map, q, P_map, p, x_sz):
    if p == 1:
        return np.zeros(x_sz - 1)
        
    # Precompute c and cumhist
    c = np.zeros(p, dtype=np.int32)
    for i in range(n):
        c[P_map[i]] += 1
    c = np.cumsum(c) # Cumulative count c[i] is sum up to partition i
    
    # C logic: c is cumulative count, c[0] is count of P=0.
    
    c_log = np.zeros(p) # usually not strictly needed if we compute log on fly, but passed args
    
    cumhist = np.zeros((q, p), dtype=np.int32)
    for i in range(n):
        cumhist[Q_map[i], P_map[i]] += 1
        
    # Cumulative sum along axis 1
    for r in range(q):
        curr = 0
        for col in range(p):
            curr += cumhist[r, col]
            cumhist[r, col] = curr
            
    cumhist_log = np.zeros((q, p))
    for r in range(q):
        for col in range(p):
            if cumhist[r, col] > 0:
                cumhist_log[r, col] = np.log(float(cumhist[r, col]))
                
    return optimize_x_axis_core(c, c_log, cumhist, cumhist_log, q, p, n, x_sz)

def mine_compute_score_numba(prob: MineProblem, param: MineParameter) -> Optional[MineScore]:
    # Parameter Setup
    if param.alpha > 0.0 and param.alpha <= 1.0:
        B = max(prob.n ** param.alpha, 4.0)
    elif param.alpha >= 4:
        B = min(param.alpha, prob.n)
    else:
        return None
        
    score_n = max(int(np.floor(B / 2.0)), 2) - 1
    score_m = np.zeros(score_n, dtype=np.int32)
    for i in range(score_n):
        val = np.floor(B / float(i + 2))
        score_m[i] = int(val) - 1
        
    M_list = [np.zeros(score_m[i]) for i in range(score_n)]
    
    # Data Prep
    xx = np.array(prob.x).astype(np.float64)
    yy = np.array(prob.y).astype(np.float64)
    n = prob.n
    
    ix = np.argsort(xx)
    iy = np.argsort(yy)
    
    xx_sorted = xx[ix]
    yy_sorted_by_x = yy[ix]
    
    yy_sorted = yy[iy]
    xx_sorted_by_y = xx[iy]
    
    # --- Main Loop (X vs Y) ---
    for i in range(score_n):
        k = max(int(param.c * (score_m[i] + 1)), 1)
        Q_map, q = equipartition_y_axis(yy_sorted, n, i + 2)
        if q == 0: continue
        
        sample_to_Q = np.zeros(n, dtype=np.int32)
        sample_to_Q[iy] = Q_map
        Q_map_by_x = sample_to_Q[ix]
        
        P_map, p = get_superclumps_partition(xx_sorted, n, k, Q_map_by_x)
        
        limit_val = score_m[i] + 1
        is_mic_e = (param.est == EST_MIC_E)
        if is_mic_e:
            limit_val = min(i + 2, score_m[i] + 1)
        
        # Core DP
        score_vec = optimize_x_axis(xx_sorted, yy_sorted_by_x, n, Q_map_by_x, q, P_map, p, limit_val)
        
        # Store results
        count = len(score_vec)
        if count > 0:
             limit_fill = min(count, len(M_list[i]))
             M_list[i][:limit_fill] = score_vec[:limit_fill]

    # --- Main Loop (Y vs X) ---
    for i in range(score_n):
        k = max(int(param.c * (score_m[i] + 1)), 1)
        Q_map, q = equipartition_y_axis(xx_sorted, n, i + 2)
        if q == 0: continue
        
        sample_to_Q = np.zeros(n, dtype=np.int32)
        sample_to_Q[ix] = Q_map
        Q_map_by_y = sample_to_Q[iy]
        
        P_map, p = get_superclumps_partition(yy_sorted, n, k, Q_map_by_y)
        
        limit_val = score_m[i] + 1
        is_mic_e = (param.est == EST_MIC_E)
        if is_mic_e:
            limit_val = min(i + 2, score_m[i] + 1)
            
        score_vec = optimize_x_axis(yy_sorted, xx_sorted_by_y, n, Q_map_by_y, q, P_map, p, limit_val)
        
        for j in range(len(score_vec)):
            if j < len(M_list) and i < len(M_list[j]):
                if param.est == EST_MIC_APPROX:
                    M_list[j][i] = max(M_list[j][i], score_vec[j])
                else:
                     # For MIC_E
                     M_list[j][i] = score_vec[j]

    return MineScore(score_n, score_m, M_list)

# Alias for compatibility if needed
mine_compute_score = mine_compute_score_numba

# --- Stats Functions ---

def mine_mic(score: MineScore) -> float:
    mic = 0.0
    for i in range(score.n):
        if len(score.M[i]) > 0:
            m_max = np.max(score.M[i])
            if m_max > mic:
                mic = m_max
    return mic

def mine_mas(score: MineScore) -> float:
    mas = 0.0
    for i in range(score.n):
        for j in range(len(score.M[i])):
            if j < score.n and i < len(score.M[j]):
                val = abs(score.M[i][j] - score.M[j][i])
                if val > mas:
                    mas = val
    return mas

def mine_mev(score: MineScore) -> float:
    mev = 0.0
    for i in range(score.n):
        for j in range(len(score.M[i])):
            if i == 0 or j == 0:
                if score.M[i][j] > mev:
                    mev = score.M[i][j]
    return mev

def mine_mcn(score: MineScore, eps: float = 0.0) -> float:
    mic = mine_mic(score)
    threshold = (1.0 - eps) * mic
    min_log_xy = float('inf')
    found = False
    for i in range(score.n):
        for j in range(len(score.M[i])):
            if score.M[i][j] + 1e-7 >= threshold:
                log_xy = np.log2((i + 2) * (j + 2))
                if log_xy < min_log_xy:
                    min_log_xy = log_xy
                    found = True
    if not found: return 0.0
    return min_log_xy

def mine_mcn_general(score: MineScore) -> float:
    mic = mine_mic(score)
    threshold = mic * mic
    min_log_xy = float('inf')
    found = False
    for i in range(score.n):
        for j in range(len(score.M[i])):
            if score.M[i][j] + 1e-7 >= threshold:
                log_xy = np.log2((i + 2) * (j + 2))
                if log_xy < min_log_xy:
                    min_log_xy = log_xy
                    found = True
    if not found: return 0.0
    return min_log_xy

def mine_tic(score: MineScore, norm: bool = True) -> float:
    tic = 0.0
    count = 0
    for i in range(score.n):
        tic += np.sum(score.M[i])
        count += len(score.M[i])
    if norm and count > 0:
        tic /= count
    return tic

def mine_gmic(score_orig: MineScore, p: float = 0.0) -> float:
    gmic = 0.0
    count = 0
    for i in range(score_orig.n):
        for j in range(len(score_orig.M[i])):
            B_sub = (i + 2) * (j + 2)
            n_sub = max(int(np.floor(B_sub / 2.0)), 2) - 1
            n_sub = min(n_sub, score_orig.n)
            
            c_star_val = 0.0
            for k in range(n_sub):
                m_lim = int(np.floor(B_sub / float(k + 2))) - 1
                m_lim = min(m_lim, len(score_orig.M[k]))
                if m_lim > 0:
                    row_max = np.max(score_orig.M[k][:m_lim])
                    if row_max > c_star_val:
                        c_star_val = row_max
            if p == 0.0:
                if count == 0: gmic = 1.0
                gmic *= c_star_val
            else:
                gmic += c_star_val ** p
            count += 1
    if count == 0: return 0.0
    if p == 0.0:
        gmic = gmic ** (1.0 / count)
    else:
        gmic = (gmic / count) ** (1.0 / p)
    return gmic
