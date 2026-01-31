# What is String Grammar Fuzzy Clustering?

String Grammar Fuzzy Clustering is a clustering framework designed for syntactic or structural pattern recognition, where each data instance is represented not as a numeric vector but as a string that encodes structural information.

Unlike conventional numerical clustering method (e.g., Fuzzy C-Means), which assume that data have a fixed-length feature vector whereas structural clustering method operates directly on string data whose lengths and internal structures may vary.

In this approach, each pattern is described by a sequence of primitives (symbols) defined by grammatical rules. This is similar to how a sentence is formed from characters following syntax rules.

To measure similarity between strings, the method employs the Levenshtein distance[1], which counts the minimum number of edit operations (insertions, deletions, substitutions) required to transform one string into another.

The "fuzzy" aspect of this framework allows each string to belong to multiple clusters, with a membership degree that reflects how strongly it is associated with each cluster. This provides a more flexible and realistic clustering behavior compared to traditional "hard" clustering, which forces each sample to belong to only one group.

# About This Library

This Python library introduces an algorithm belonging to the String Grammar Fuzzy Clustering framework, namely the String Grammar Fuzzy C-Medians (sgFCMed).

## String Grammar Fuzzy C-Medians (sgFCMed)[2]

The sgFCMed algorithm extends the conventional Fuzzy C-Medians to handle string-based or syntactic data by using the Levenshtein distance instead of Euclidean distance. Each cluster is represented by a prototype string that minimizes the weighted sum of distances to all strings in the cluster, and each sample has a fuzzy membership value indicating its degree of belonging to different clusters. This method effectively clusters variable-length symbolic data, capturing structural similarity without requiring vector representations.

**Key Features:**

- Works directly on string-encoded or grammar-based data
- Uses Levenshtein distance for similarity measurement
- Maintains a fuzzy membership matrix (U) that quantifies how strongly each string belongs to each cluster
- Parallelized medoid and modified median updates
- Ideal for datasets with overlapping but relatively clean patterns

**\*\*Please be noted that this sgFCMed can be used for academic and research purposes only. Please also cite this paper [2].\*\***

## Reference

[1] S. K. Fu, Syntactic Pattern Recognition and Applications, 1982, Prentice-Hall, Zbl0521.68091.

[2] Atcharin Klomsae, Sansanee Auephanwiriyakul, and Nipon Theera-Umpon, “A Novel String Grammar Fuzzy C-Medians,” Proceedings of the 2015 IEEE International Conference on Fuzzy Systems, Istanbul, Turkey, August 2015.

# Installation

You can install the library using pip:

```bash
pip install sgFCMed
```

# USAGE

## Example Code

```python
import random
from sgFCMed import SGFCMed # Import the clustering class

if __name__ == "__main__":
    # Set random seed for reproducibility
    random.seed(42)

    # Define a list of strings to cluster
    data = ["book", "back", "boon", "cook", "look", "cool", "kick", "lack", "rack", "tack"]

    # Create the model with 2 clusters and fuzzifier m=2.0
    model = SGFCMed(C=2, m=2.0)

    # Fit the model on the data
    model.fit(data)

    # Print the final prototype strings representing each cluster
    print("Prototypes:", model.prototypes())

    # Print the fuzzy membership matrix for each input string
    print("\nMembership Matrix (U):")
    for s, u in zip(data, model.membership()):
        print(f"{s:>6} → {[round(val, 3) for val in u]}")

    # Define new strings to classify using the trained model
    new_data = ["hack", "rook", "cook"]

    # Predict the cluster index (0 or 1) for each new string
    preds = model.predict(new_data, model.prototypes())
    print("\nPredictions:")
    for s, c in zip(new_data, preds):
        print(f"{s} → Cluster {c+1}")
```
