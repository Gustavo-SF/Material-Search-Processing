import unicodedata as unic
import string
import re

from nltk import pos_tag
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet


def get_wordnet_pos(pos_tag):
    if pos_tag.startswith("J"):
        return wordnet.ADJ
    elif pos_tag.startswith("V"):
        return wordnet.VERB
    elif pos_tag.startswith("N"):
        return wordnet.NOUN
    elif pos_tag.startswith("R"):
        return wordnet.ADV
    else:
        return wordnet.NOUN


# multiple functions to clean the t
def clean_text(text):
    # clean any unicode formatting left
    text = unic.normalize("NFKD", text)
    # lower text
    text = text.lower()
    # tokenize text and remove puncutation
    text = [word.strip(string.punctuation) for word in text.split(" ")]
    # replace the rest of the punctuation by space
    text = " ".join(text)
    text = [w for w in re.split("\.|\-|\s|\,|\(|\_|\d", text)]
    # remove words that contain numbers
    text = [word for word in text if not any(c.isdigit() for c in word)]
    # remove stop words | Not really needed
    stop = stopwords.words("english")
    text = [x for x in text if x not in stop]
    # remove empty
    text = [t for t in text if len(t) > 1]
    # pos tag text
    pos_tags = pos_tag(text)
    # lemmatize text
    text = [
        WordNetLemmatizer().lemmatize(t[0], get_wordnet_pos(t[1])) for t in pos_tags
    ]
    # remove words with only one letter
    text = [t for t in text if len(t) > 2]
    # join all
    text = " ".join(text)
    return text
