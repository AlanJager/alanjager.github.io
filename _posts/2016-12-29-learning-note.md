---
layout: post
title: First post!
subtitle: This is a subtitle!
tags: [note, machine learning]
---

"""Softmax."""
    scores = [3.0, 1.0, 0.2]

    import numpy as np

    def softmax(x):
        """Compute softmax values for each sets of scores in x."""
        e_x = np.exp(x - np.max(x))
        return e_x / e_x.sum()

    print(softmax(scores))

    # Plot softmax curves
    import matplotlib.pyplot as plt
    x = np.arange(-2.0, 6.0, 0.1)
    scores = np.vstack([x, np.ones_like(x), 0.2 * np.ones_like(x)])

    plt.plot(x, softmax(scores).T, linewidth=2)
    plt.show()