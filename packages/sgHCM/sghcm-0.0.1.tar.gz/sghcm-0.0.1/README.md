# What is String Grammar Fuzzy Clustering?

String Grammar Fuzzy Clustering is a clustering framework designed for syntactic or structural pattern recognition, where each data instance is represented not as a numeric vector but as a string that encodes structural information.

Unlike conventional numerical clustering method (e.g., Hard C-Means or Fuzzy C-Means), which assume that data have a fixed-length feature vector whereas structural clustering method operates directly on string data whose lengths and internal structures may vary.

In this approach, each pattern is described by a sequence of primitives (symbols) defined by grammatical rules. This is similar to how a sentence is formed from characters following syntax rules.

To measure similarity between strings, the method employs the Levenshtein distance [1], which counts the minimum number of edit operations (insertions, deletions, substitutions) required to transform on string into another.

The "fuzzy" aspect of this framework allows each string to belong to multiple clusters, with a membership degree that reflects how strongly it is associated with each cluster. This provides a more flexible and realistic clustering behavior compared to traditional "hard" clustering, which forces each sample to belong to only one group.

# About This Library

This Python library introduces an algorithm belonging to the String Grammar Clustering framework, namely the String Grammar Hard C-Means (sgHCM).

## String Grammar Hard C-Means (sgHCM)[1,2]

The sgHCM (String Grammar Hard C-Means) algorithm is an extension of the conventional Hard C-Means (HCM) [3] clustering algorithm designed for a string data set. Since strings are not numeric vectors, traditional distance measures such as Euclidean distance cannot be applied. Therefore, sgHCM employs the Levenshtein distance to measure the dissimilarity between strings based on the minimum number of edit operations required to transform one string into another. The objective of sgHCM is to assign each string observation to exactly one cluster.

**Key Features:**

- Designed for clustering syntactic string patterns.
- Uses the Levenshtein distance to measure dissimilarity between strings.
- Represents each cluster by a string grammar-based prototype.
- Assigns each string to exactly one cluster (hard clustering).
- Simple and analytically interpretable clustering framework.

**\*\*Please be noted that this sgHCM can be used for academic and research purposes only. Please also cite this paper [1,2].\*\***

## Reference

[1] S. K. Fu, Syntactic Pattern Recognition and Applications, Prentice-Hall, 1982, Zbl0521.68091.

[2] Sansanee Auephanwiriyakul, and Prach Chaisatian, “Static Hand Gesture Translation Using String Grammar Hard C-Means”, The Fifth International Conference on Intelligent Technologies, Houston, Texas, USA., December 2004.

[3] J.C. Bezdek, Pattern Recognition with Fuzzy Objective Function Algorithms, Springer US., 1981.

# Installation

You can install the library using pip:

```bash
pip install sgHCM
```

# USAGE

## Example Code

```python
import random
from sgHCM import SGHCM # Import the clustering class

if __name__ == "__main__":
    # Set random seed for reproducibility
    random.seed(42)

    # Define a list of strings to cluster
    data = ["book", "back", "boon", "cook", "look", "cool", "kick", "lack", "rack", "tack"]

    # Create the model with 2 clusters and fuzzifier m=2.0
    model = SGHCM(C=2)

    # Fit the model on the data
    model.fit(data)

    # Print the final prototype strings representing each cluster
    print("Prototypes:", model.prototypes())

    # Define new strings to classify using the trained model
    new_data = ["hack", "rook", "cook"]

    # Predict the cluster index (0 or 1) for each new string
    preds = model.predict(new_data, model.prototypes())
    print("\nPredictions:")
    for s, c in zip(new_data, preds):
        print(f"{s} → Cluster {c+1}")
```
