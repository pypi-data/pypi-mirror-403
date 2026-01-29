"""
Clustering algorithms for identity resolution.

After scoring pairs of records, we need to group all matches into clusters.
The key challenge is transitive closure: if A matches B, and B matches C,
then A, B, and C should all be in the same cluster, even if A and C were
never directly compared.

Union-Find (Disjoint Set Union) solves this efficiently:
- union(a, b): Merge the clusters containing a and b
- find(x): Find which cluster x belongs to
- Path compression: Makes repeated lookups O(1) amortized
"""

from collections.abc import Iterable

import pandas as pd


class UnionFind:
    """Union-Find data structure with path compression for transitive clustering.

    This is the standard algorithm for grouping matches transitively.
    If you union(1, 2) and union(2, 3), then find(1) == find(3).

    Time complexity:
    - union: O(α(n)) amortized (nearly constant)
    - find: O(α(n)) amortized (nearly constant)
    - get_clusters: O(n)

    Examples:
        >>> uf = UnionFind([1, 2, 3, 4, 5])
        >>> uf.union(1, 2)
        >>> uf.union(2, 3)  # Transitive: 1-2-3 now in same cluster
        >>> uf.find(1) == uf.find(3)
        True
        >>> uf.get_clusters()
        {1: [1, 2, 3], 4: [4], 5: [5]}
    """

    def __init__(self, elements: Iterable[int]) -> None:
        """Initialize Union-Find with element IDs.

        Args:
            elements: Iterable of unique integer identifiers (e.g., DataFrame indices)
        """
        self.parent: dict[int, int] = {x: x for x in elements}
        self.rank: dict[int, int] = {x: 0 for x in elements}

    def find(self, x: int) -> int:
        """Find the root/representative of the cluster containing x.

        Uses path compression: all nodes along the path point directly
        to the root after this call, making future lookups faster.

        Args:
            x: Element to find the cluster for

        Returns:
            Root element ID (cluster identifier)
        """
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])  # Path compression
        return self.parent[x]

    def union(self, a: int, b: int) -> None:
        """Merge the clusters containing a and b.

        Uses union by rank: the smaller tree is attached under the
        larger tree's root, keeping the tree balanced.

        Args:
            a: First element
            b: Second element
        """
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            # Union by rank: attach smaller tree under larger tree
            if self.rank[ra] < self.rank[rb]:
                ra, rb = rb, ra
            self.parent[rb] = ra
            if self.rank[ra] == self.rank[rb]:
                self.rank[ra] += 1

    def get_clusters(self) -> dict[int, list[int]]:
        """Return mapping of cluster root → member IDs.

        Returns:
            Dict where keys are cluster identifiers (root element IDs)
            and values are lists of all elements in that cluster.

        Examples:
            >>> uf = UnionFind([1, 2, 3])
            >>> uf.union(1, 2)
            >>> uf.get_clusters()
            {1: [1, 2], 3: [3]}
        """
        clusters: dict[int, list[int]] = {}
        for x in self.parent:
            root = self.find(x)
            if root not in clusters:
                clusters[root] = []
            clusters[root].append(x)
        return clusters

    def connected(self, a: int, b: int) -> bool:
        """Check if two elements are in the same cluster.

        Args:
            a: First element
            b: Second element

        Returns:
            True if a and b are in the same cluster
        """
        return self.find(a) == self.find(b)


def cluster_records(
    pairs: pd.DataFrame,
    record_ids: list[int],
    threshold: float,
    score_col: str = "score",
    left_col: str = "left",
    right_col: str = "right",
) -> dict[int, list[int]]:
    """Cluster records based on scored pairs above a threshold.

    Takes a DataFrame of scored pairs and groups records transitively.
    All pairs with score >= threshold are merged.

    Args:
        pairs: DataFrame with columns for left ID, right ID, and score
        record_ids: List of all record IDs (including those without pairs)
        threshold: Minimum score to consider a match (e.g., 0.7)
        score_col: Name of the score column
        left_col: Name of the left record ID column
        right_col: Name of the right record ID column

    Returns:
        Dict mapping cluster ID → list of record IDs in that cluster

    Examples:
        >>> pairs = pd.DataFrame({
        ...     "left": [0, 1],
        ...     "right": [1, 2],
        ...     "score": [0.9, 0.8]
        ... })
        >>> cluster_records(pairs, [0, 1, 2, 3], threshold=0.7)
        {0: [0, 1, 2], 3: [3]}  # 0-1-2 clustered, 3 alone
    """
    uf = UnionFind(record_ids)

    # Union all pairs above threshold
    for _, row in pairs.iterrows():
        if row[score_col] >= threshold:
            uf.union(int(row[left_col]), int(row[right_col]))

    return uf.get_clusters()
