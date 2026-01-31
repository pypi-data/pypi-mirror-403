import math
import pytest
import random
import multiprocessing
from sgUPFCMed.sgUPFCMed import SGUPFCMed
from unittest.mock import patch
import sgUPFCMed.sgUPFCMed as sgUPFcmed

@pytest.fixture
def data():
    """
    Example 20 data from the Copenhagen Chromosome Data set
    (Chromosome type 22, file b)
    """
    return [
        "A=A====D==d===A==a=======a=a",
        "A=Aa=====E==d==A===b====Aa=a",
        "A=Aa===E==e===A====a===A=a=a",
        "AA==a====E===d==A==b=Aa=A=aa",
        "A=A=====D==e===A==a==A==a=a",
        "Ba=Aa===E==d==A=a===a=A=a=a",
        "A=B=a==D===c==A===b==A=b==a",
        "AA==a===E==e==A====a==A=a=a",
        "B==A==a==D==d===A==a==A=a=b",
        "AA=a===E===e===A===a===A=aa",
        "A=====E===c==A=====bA=b===a",
        "A=Aa==E=====c===A==b==A=b=a",
        "AA=a===E===e===A==a==A==a=a",
        "B=A=a===D===d=====Aa=A==b=a",
        "B===Aa==D==c===A==a=A===b=b",
        "AA==a==E===d==A==a=Aa=A=a=b",
        "AA=a====E==d==A==aAa=A==a=b",
        "A=A=a===E===e===A===a=A=a=a",
        "AA===B=a=C===d==A===aA==b=a",
        "A=A=a====E==e===A=a==A==a=a",
    ]

def test_initialization():
    """
    Ensure that model initialization correctly sets parameters.
    """
    model = SGUPFCMed(C=2, a=1, b=4, m=2.0, eta=2.0, max_iter=5, tol=0.1,
                refine_with_modified_median=True,
                 medoid_topK=4, mm_jump_topK=2,
                 enforce_unique=True, min_proto_distance=1,
                 n_jobs=None, seed=48,
                 use_obj_stop=False, obj_tol=1e-6)
    assert model.C == 2
    assert model.a == 1
    assert model.b == 4
    assert model.m == 2.0
    assert model.eta == 2.0
    assert model.max_iter == 5
    assert model.tol == 0.1
    assert model.refine_with_modified_median is True
    assert model.medoid_topK == 4
    assert model.mm_jump_topK == 2
    assert model.enforce_unique is True
    assert model.min_proto_distance == 1
    assert model.n_jobs is not None
    assert model.seed == 48
    assert model.use_obj_stop is False
    assert model.obj_tol == 1e-6

def test_lev_cached(data):
    """ 
    Test the correctness of the Levenshtein distance function 
    (Internal function used by the algorithm)
    """
    model = SGUPFCMed(C=2)
    assert model._d(data[0], data[1]) == 7
    assert model._d("", data[2]) == len(data[2])
    assert model._d(data[3], "") == len(data[3])
    assert model._d(data[4], data[4]) == 0
    assert model._d("","") == 0
    
def test_init_prototypes(data):
    """
    Tests that the _smart_init method correctly initializes the specified
    number (C) of prototypes (cluster centers) and that all prototypes 
    are of the correct type (string).
    """
    model = SGUPFCMed(C=4)
    init_protos = model._smart_init(data)
    assert len(init_protos) == 4
    assert all(isinstance(p, str) for p in init_protos)

def test_update_prototype_medoid(data):
    """
    Tests the _update_prototype_medoid method ensures the returned prototype 
    (medoid) is a valid string and is an element of the original data set.
    """
    model = SGUPFCMed(C=2)
    W = [random.random() for _ in data]
    with multiprocessing.Pool(multiprocessing.cpu_count() ) as pool:
        result = model._update_prototype_medoid(0, data, W, pool)
    assert isinstance(result, str)
    assert result in data

def test_update_prototype_medoid_all_violated(data):
    """
    Ensure that when all candidates violate hard uniqueness (scored = []),
    the method falls back to using results from candidate_score_weighted.
    """
    model = SGUPFCMed(C=2)
    model.prototypes_ = ["abc", "xyz"] 

    with patch.object(model, "_violates_hard_uniqueness", return_value=True):
        W = [random.random() for _ in data]
        with multiprocessing.Pool(2) as pool:
            result = model._update_prototype_medoid(0, data, W, pool)

    assert isinstance(result, str)
    assert result in data

def test_modified_median_refine(data):
    """
    Tests the _modified_median_refine method ensures that the refined string 
    prototype is still a string and maintains a minimum level of similarity 
    to its starting point.
    """
    model = SGUPFCMed(C=2)
    start = data[0]
    W = [random.random() for _ in data]
    with multiprocessing.Pool(multiprocessing.cpu_count() ) as pool:
        refined = model._modified_median_refine(0, start, data, W, pool)
    assert isinstance(refined, str)
    # refined string should not be completely unrelated
    common_chars = len(set(start) & set(refined))
    assert common_chars >= 2  # expect at least some similarity

def fake_candidate_score_weighted(args):
    """
    It simply returns the candidate and a dummy score.
    """
    cand, S, W_i = args
    return cand, len(cand) 

def test_modified_median_refine_all_violated(data):
    """
    Ensure that when all candidates violate hard uniqueness (scored = []),
    the method correctly falls back to using results from candidate_score_weighted.
    """
    model = SGUPFCMed(C=2)
    model.mm_jump_topK = 2
    model.prototypes_ = ["abc", "xyz"]

    S = data[:3] if len(data) >= 3 else ["abc", "abd", "aac"]
    W_i = [random.random() for _ in S]
    start = S[0]

    with patch.object(model, "_violates_hard_uniqueness", return_value=True), \
         patch.object(sgUPFcmed, "candidate_score_weighted", fake_candidate_score_weighted):

        with multiprocessing.Pool(2) as pool:
            refined = model._modified_median_refine(0, start, S, W_i, pool)

    assert isinstance(refined, str)
    assert len(refined) > 0

def test_cs_computes_weighted_distance():
    """
    Tests the _cs method to ensure it correctly computes the weighted distance 
    between a candidate string and a set of strings with associated weights.
    """
    model = SGUPFCMed()
    cand = "cat"
    S = ["cat", "bat", "dog"]
    W = [1.0, 0.5, 0.2]
    cand_out, total = model._cs((cand, S, W))
    assert cand_out == cand
    assert isinstance(total, float)
    assert total >= 0
    _, total2 = model._cs((cand, S, [0.0, 0.0, 0.0]))
    assert total2 == 0.0

def test_compute_beta(data):
    """
    Tests the compute_beta method to ensure it returns a positive beta value 
    based on the average distance to a global medoid.
    """
    model = SGUPFCMed(C=2)
    with multiprocessing.Pool(multiprocessing.cpu_count() ) as pool:
        beta = model._compute_beta(data, pool)
    assert isinstance(beta, float)
    assert beta > 0.0
    assert beta == 7.1

def test_pipeline(data):
    """
    Tests the full clustering pipeline (initialization, fitting, and result validation).
    It checks the integrity of the final prototypes, membership matrices (U_,T_), 
    parameter (a,b,m,eta) and the objective function value (J).
    """
    model = SGUPFCMed(C=3, max_iter=5)
    model.fit(data)
    assert len(model.prototypes()) == 3
    assert all(isinstance(p, str) for p in model.prototypes())

    for row in model.membership():
        assert all(0 <= u <= 1 for u in row)
        s = sum(row)
        assert abs(s - 1) < 1e-6

    for row in model.typicality():
        assert all(0 <= t <= 1 for t in row)

    assert model.a > 0.0
    assert model.b > 0.0        
    assert model.m > 1.0
    assert model.eta > 1.0

    J = model._objective(data)
    assert math.isfinite(J)

# --------------------------------------------------------------------------
# Common error handling for this algorithm
# --------------------------------------------------------------------------
def test_fit_with_empty_data():
    """
    Tests that the fit method correctly raises a ValueError when the input 
    data list is empty, as the model cannot be trained without samples.
    """
    model = SGUPFCMed(C=3)
    with pytest.raises(ValueError):
        model.fit([])

def test_more_clusters_than_samples(data):
    """
    Tests that the fit method raises a ValueError if the number of requested 
    clusters (C) is greater than the total number of data samples.
    """
    model = SGUPFCMed(C=30, max_iter=1)
    with pytest.raises(ValueError):
        model.fit(data)

def test_enforce_unique_prototypes(data):
    """
    Tests that when enforce_unique=True, the final set of learned prototypes 
    (model.prototypes()) contains no duplicate strings.
    """
    model = SGUPFCMed(C=2, enforce_unique=True)
    model.fit(data)
    assert len(set(model.prototypes())) == len(model.prototypes())

def test_beta_zero_raises_error():
    data = ["same", "same", "same"]

    model = SGUPFCMed(C=2)

    with pytest.raises(ValueError, match="beta is zero"):
        model.fit(data)

# --------------------------------------------------------------------------
# Test BaseClustering helpers
# --------------------------------------------------------------------------
def test_violates_hard_uniqueness():
    model = SGUPFCMed(C=2, enforce_unique=True)
    model.prototypes_ = ["aaa", "bbb"]
    assert model._violates_hard_uniqueness(1, "aaa") == True
    assert model._violates_hard_uniqueness(0, "aba") == False

def test_predict_clusters():
    model = SGUPFCMed(C=2)
    model.prototypes_ = ["aaa", "bbb"]
    S = ["aaa", "aab", "bbc"]
    preds = model.predict(S, model.prototypes())
    assert len(preds) == len(S)
    assert all(p in [0, 1] for p in preds)