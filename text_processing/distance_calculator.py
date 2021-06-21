import numpy as np
import editdistance as ed


def dist_sentence(token1, token2):
    """Distance for sentence adapted from levenshtein but with no fixed order."""
    initial = token1 + "|" + token2

    token1 = token1.split(" ")
    token2 = token2.split(" ")

    m = len(token1)
    n = len(token2)

    if (m == 0) or (n == 0):
        return 0

    ln = max(m, n)
    ln_max = ln

    # Remove identical words before checking if words are similar.
    to_remove = []
    for c in token1:
        if c in token2:
            to_remove.append(c)

    for c in set(to_remove):
        token1.remove(c)
        token2.remove(c)
        ln -= 1
        n -= 1
        m -= 1

    # Initialize distance variable
    distance = 0

    # Find similar words
    for i, s1 in enumerate(token1):
        if token2:
            values = np.zeros((1, n))
            for j, s2 in enumerate(token2):
                l_word = max(len(s1), len(s2))
                values[0, j] = ed.eval(s1, s2) / l_word
            try:
                value = np.amin(values)
            except:
                print(initial)
            if value < 0.33:
                index = np.argmax(values)
                # Add relative leven distance to distance
                distance += value
                # Remove the tokens
                token1.remove(token1[i])
                token2.remove(token2[index])
                ln -= 1
                n -= 1

    # Add the missing values that weren't matched
    distance += ln

    return int((distance / ln_max) * 100)
