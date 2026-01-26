def normalize_pattern(p: str) -> str:
    p = p.lower()

    mapping = {
        "kadane": "Dynamic Programming (Tabulation)",
        "boyer": "Greedy Pattern",
        "two pointer": "Two Pointer Pattern",
        "sliding": "Sliding Window Pattern",
        "prefix": "Prefix Sum Pattern",
        "hash": "HashMap Pattern",
        "binary search": "Binary Search Pattern",
        "monotonic": "Monotonic Stack",
        "queue": "Queue Pattern",
        "stack": "Stack Pattern",
        "memo": "Dynamic Programming (Memoization)",
        "dp": "Dynamic Programming (Tabulation)",
        "greedy": "Greedy Pattern",
        "divide": "Divide and Conquer",
        "meet": "Meet-in-the-Middle",
        "quickselect": "QuickSelect (Selection Algorithm)",
        "trie": "Trie (Prefix Tree)",
        "union find": "Union Find (Disjoint Set)",
        "topological": "Topological Sort",
        "dijkstra": "Dijkstra’s Algorithm",
        "bellman": "Bellman-Ford Algorithm",
        "floyd": "Floyd-Warshall Algorithm",
        "prim": "Prim's Algorithm (MST)",
        "kruskal": "Kruskal's Algorithm (MST)",
        "heap": "Heap / Priority Queue (Top K Elements)",
        "segment": "Segment Tree / Fenwick Tree",
        "fenwick": "Segment Tree / Fenwick Tree",
        "bit": "Bit Manipulation",
        "kmp": "String Matching (KMP / Rabin-Karp)",
        "rabin": "String Matching (KMP / Rabin-Karp)",
        "matrix": "Matrix Manipulation",
        "reservoir": "Reservoir Sampling",
        "binary lifting": "Binary Lifting"
    }

    for key in mapping:
        if key in p:
            return mapping[key]

    return p
