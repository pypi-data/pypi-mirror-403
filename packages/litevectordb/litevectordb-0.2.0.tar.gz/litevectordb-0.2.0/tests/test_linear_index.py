import numpy as np
from litevectordb.index.linear import LinearIndex

def test_linear_index_search():
    index = LinearIndex(dim=3)

    ids = ["a", "b", "c"]
    vectors = np.array([
        [1, 0, 0],
        [0, 1, 0],
        [0.9, 0.1, 0]
    ])

    index.add(ids, vectors)

    query = np.array([1, 0, 0])
    results = index.search(query, k=2)

    assert results[0][0] == "a"
    # "a" matches perfectly (dot=1.0). "c" is close (dot=0.9). "b" is orthogonal (dot=0.0).
    # So results should be "a" then "c" (if k=2) or just "a" if k=1.
    # The test checks results[0][0] == "a".
