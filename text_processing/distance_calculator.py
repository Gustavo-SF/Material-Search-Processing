import numpy as np
import editdistance as ed


def dist_sentence(sentence_1, sentence_2):
    """Distance for sentence adapted from levenshtein but with no fixed order."""
    initial = sentence_1 + "|" + sentence_2
    
    sentence_1_set = set(sentence_1.split(' '))
    sentence_2_set = set(sentence_2.split(' '))
    
    # Get the maximum length of the sentences to use in the end
    # when we have to calculate the percentage of difference between 
    # both sentences.
    ln_max = max(len(sentence_1_set), len(sentence_2_set))
    
    # Remove common words
    sentence_1_list = list(sentence_1_set - sentence_2_set)
    sentence_2_list = list(sentence_2_set - sentence_1_set)
    
    # Get the current lengths
    m = len(sentence_1_list)
    n = len(sentence_2_list)
    ln = max(m, n)

    # Initialize distance variable
    distance = 0
    
    # Find similar words
    for i, s1 in enumerate(sentence_1_list):
        # Continue if there are still values in sentence_2 list
        if sentence_2_list:
            values = np.zeros((1, n))
            for j, s2 in enumerate(sentence_2_list):
                l_word = max(len(s1),len(s2))
                values[0,j] = ed.eval(s1, s2) / l_word
            try:
                value = np.amin(values)
            except:
                print(initial)
            if value < 0.33:
                index = np.argmin(values)
                # Add relative leven distance to distance
                distance += value
                # Remove the tokens
                sentence_2_list.remove(sentence_2_list[index])
                ln -= 1
                n -= 1
    
    # Add the missing values that weren't matched
    distance += ln
    
    return int((distance / ln_max) * 100)
