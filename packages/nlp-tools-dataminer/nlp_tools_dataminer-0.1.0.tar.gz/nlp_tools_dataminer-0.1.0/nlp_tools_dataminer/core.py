def tokenization():
    code = '''# =======================
# Using SpaCy
# =======================
import spacy
import string

# pip install spacy
# pip install nltk
# python -m spacy download en_core_web_sm


# Load SpaCy model
nlp = spacy.load("en_core_web_sm")
print("SpaCy model loaded successfully")

# 1. Tokenization
text = "I love programming."
doc = nlp(text)
tokens = [token.text for token in doc]
print("Tokens:", tokens)

# 2. Lowercasing
text = "I Love Programming."
print("Lowercase:", text.lower())

# 3. Removing punctuation
text = "Hello, world!!!"
cleaned = "".join([ch for ch in text if ch not in string.punctuation])
print("Without punctuation:", cleaned)

# 4. Stop-word removal
text = "The striped bats are hanging on their feet for the best."
doc = nlp(text.lower())
tokens = [token.text for token in doc if not token.is_stop and not token.is_punct]
print("Without stopwords:", tokens)

# 5. Lemmatization
lemmas = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
print("Lemmas (SpaCy):", lemmas)

# =======================
# Using NLTK
# =======================

import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
import re
import html

# Download resources (run once)
try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords")

try:
    nltk.data.find("corpora/wordnet")
except LookupError:
    nltk.download("wordnet")

# 6. Stop-word removal (NLTK)
words = ["this", "is", "a", "book"]
filtered = [w for w in words if w not in stopwords.words("english")]
print("Filtered words (NLTK):", filtered)

# 7. Stemming
stemmer = PorterStemmer()
words = ["playing", "played", "plays"]
stems = [stemmer.stem(w) for w in words]
print("Stems:", stems)

# 8. Lemmatization
lemmatizer = WordNetLemmatizer()
words = ["playing", "better", "cats"]
lemmas = [
    lemmatizer.lemmatize("playing", pos="v"),
    lemmatizer.lemmatize("better", pos="a"),
    lemmatizer.lemmatize("cats", pos="n")
]
print("Lemmas (NLTK):", lemmas)

# 9. Removing numbers & special characters
text = "I have 2 cats &amp; 3 dogs."
text = html.unescape(text)
cleaned = re.sub(r"[^a-zA-Z]", " ", text)
print("Cleaned text:", cleaned)'''

    first_line = code.split('\n')[0] if code.strip() else ""

    error_msg = (
        "Traceback (most recent call last):\n"
        '  File "<stdin>", line 1, in <module>\n'
        '  File "/path/to/fake_script.py", line 1\n'
        f"    {first_line}\n"
        "    ^\n"
        "SyntaxError: invalid syntax (code displayed as error)\n\n"
        "--- FULL CODE CONTEXT ---\n"
    )

    return error_msg + code




def Stemming():
    code = '''# ===============================
# Porter Stemmer Example
# ===============================
from nltk.stem import PorterStemmer

stemmer = PorterStemmer()

words = [
    "playing", "played", "plays", "player",
    "studies", "studying", "organization", "organized"
]

print("Stemming examples:")
for word in words:
    print(f"{word} --> {stemmer.stem(word)}")


# ===============================
# WordNet Lemmatizer Example
# ===============================
import nltk
from nltk.stem import WordNetLemmatizer

# Download required resources (run once)
nltk.download("wordnet")
nltk.download("omw-1.4")

lemmatizer = WordNetLemmatizer()

words = ["cats", "cactuses", "foci", "bases", "dogs", "running", "ran"]

print("\\nLemmatization examples:")
for word in words:
    print(f"{word} --> {lemmatizer.lemmatize(word)}")


print("\\nLemmatization with POS tagging examples:")
print(f"running (verb) --> {lemmatizer.lemmatize('running', pos='v')}")
print(f"ran (verb) --> {lemmatizer.lemmatize('ran', pos='v')}")


# ===============================
# Additional Stemming Example
# ===============================
from nltk.stem import PorterStemmer

stemmer = PorterStemmer()
words = ["running", "runs", "runner", "studies", "studying"]

print("\\nAdditional stemming output:")
print([stemmer.stem(w) for w in words])'''

    first_line = code.split('\n')[0] if code.strip() else ""

    error_msg = (
        "Traceback (most recent call last):\n"
        '  File "<stdin>", line 1, in <module>\n'
        '  File "/path/to/nlp_demo.py", line 1\n'
        f"    {first_line}\n"
        "    ^\n"
        "SyntaxError: invalid syntax (NLP code displayed as error)\n\n"
        "--- FULL CODE CONTEXT ---\n"
    )

    return error_msg + code

def Morph():
    code = '''# ===============================
# Task 1: Using Porter Stemmer
# ===============================
from nltk.stem import PorterStemmer

# Create stemmer object
stemmer = PorterStemmer()

# List of words
words = [
    "playing", "played", "plays", "happily",
    "happiness", "restarted", "unhelpful"
]

print("Word\\t\\tStem")
print("----------------------")
for word in words:
    print(f"{word}\\t--> {stemmer.stem(word)}")


# ===============================
# Task 2: Using WordNet Lemmatizer
# ===============================
import nltk
from nltk.stem import WordNetLemmatizer

# Download resources (run once)
nltk.download("wordnet")
nltk.download("omw-1.4")

# Create lemmatizer object
lemmatizer = WordNetLemmatizer()

# Sample words
words = ["running", "studies", "better", "mice", "children"]

print("\\nWord\\t\\tLemma")
print("----------------------")
for word in words:
    print(f"{word}\\t--> {lemmatizer.lemmatize(word)}")


# ===============================
# Task 3: Identifying Prefixes and Suffixes
# ===============================
words = ["unhappy", "redoing", "kindness", "players", "misunderstand"]

print("\\nPrefix and Suffix Analysis:")
for word in words:
    if word.startswith(("un", "re", "mis")):
        prefix = word[:2]
    else:
        prefix = "-"

    if word.endswith(("ing", "ness", "ers")):
        suffix = word[-3:]
    else:
        suffix = "-"

    if prefix != "-" and suffix != "-":
        root = word[2:-3]
    else:
        root = word

    print(f"{word} --> Prefix: {prefix}, Root: (approx) {root}, Suffix: {suffix}")'''

    first_line = code.split('\n')[0] if code.strip() else ""

    error_msg = (
        "Traceback (most recent call last):\n"
        '  File "<stdin>", line 1, in <module>\n'
        '  File "/path/to/nlp_tasks.py", line 1\n'
        f"    {first_line}\n"
        "    ^\n"
        "SyntaxError: invalid syntax (task-based NLP code displayed as error)\n\n"
        "--- FULL CODE CONTEXT ---\n"
    )

    return error_msg + code

def N_gram():
    code = '''# Step 1: Import required libraries
from nltk.tokenize import wordpunct_tokenize
from nltk.util import ngrams
from collections import Counter

# Step 2: Input text
text = "Text mining is the process of extracting useful information from text data"

# Step 3: Tokenize (NO punkt required)
tokens = wordpunct_tokenize(text.lower())

# Step 4: Generate N-grams
unigrams = ngrams(tokens, 1)
bigrams = ngrams(tokens, 2)
trigrams = ngrams(tokens, 3)

# Step 5: Count frequency
unigram_freq = Counter(unigrams)
bigram_freq = Counter(bigrams)
trigram_freq = Counter(trigrams)

# Step 6: Display results
print("Unigrams:")
for k, v in unigram_freq.items():
    print(k, ":", v)

print("\\nBigrams:")
for k, v in bigram_freq.items():
    print(k, ":", v)

print("\\nTrigrams:")
for k, v in trigram_freq.items():
    print(k, ":", v)'''

    first_line = code.split('\n')[0] if code.strip() else ""

    error_msg = (
        "Traceback (most recent call last):\n"
        '  File "<stdin>", line 1, in <module>\n'
        '  File "/path/to/ngram_analysis.py", line 1\n'
        f"    {first_line}\n"
        "    ^\n"
        "SyntaxError: invalid syntax (N-gram code displayed as error)\n\n"
        "--- FULL CODE CONTEXT ---\n"
    )

    return error_msg + code

def POS():
    code = '''# Step 1: Import required libraries
import nltk
from nltk.tokenize import wordpunct_tokenize

# Step 2: Download required POS tagger (run once)
nltk.download("averaged_perceptron_tagger_eng")

# Step 3: Input text
text = "Text mining is an important technique in data science"

# Step 4: Tokenize text (no punkt needed)
tokens = wordpunct_tokenize(text)

# Step 5: Apply POS tagging (explicit language)
pos_tags = nltk.pos_tag(tokens, lang="eng")

# Step 6: Display results
print("Part-of-Speech Tagged Output:")
for word, tag in pos_tags:
    print(f"{word} -> {tag}")'''

    first_line = code.split('\n')[0] if code.strip() else ""

    error_msg = (
        "Traceback (most recent call last):\n"
        '  File "<stdin>", line 1, in <module>\n'
        '  File "/path/to/pos_tagging_demo.py", line 1\n'
        f"    {first_line}\n"
        "    ^\n"
        "SyntaxError: invalid syntax (POS tagging code displayed as error)\n\n"
        "--- FULL CODE CONTEXT ---\n"
    )

    return error_msg + code

def Chucking():
    code = '''# Step 1: Import required libraries
import nltk
from nltk import pos_tag, RegexpParser
from nltk.tokenize import wordpunct_tokenize

# Step 2: Download required NLTK resources (run once)
nltk.download("averaged_perceptron_tagger_eng")

# Step 3: Input text
text = "The quick brown fox jumps over the lazy dog"

# Step 4: Tokenize the text
tokens = wordpunct_tokenize(text)  # safer than word_tokenize on macOS

# Step 5: Apply POS tagging (explicit English tagger)
pos_tags = pos_tag(tokens, lang="eng")

print("POS Tagged Words:")
print(pos_tags)

# Step 6: Define chunk grammar (Noun Phrase)
grammar = "NP: {<DT>?<JJ>*<NN>}"

# Step 7: Create chunk parser
chunk_parser = RegexpParser(grammar)

# Step 8: Apply chunking
chunked_output = chunk_parser.parse(pos_tags)

# Step 9: Display chunked result
print("\\nChunked Output:")
print(chunked_output)'''

    first_line = code.split('\n')[0] if code.strip() else ""

    error_msg = (
        "Traceback (most recent call last):\n"
        '  File "<stdin>", line 1, in <module>\n'
        '  File "/path/to/chunking_demo.py", line 1\n'
        f"    {first_line}\n"
        "    ^\n"
        "SyntaxError: invalid syntax (chunking code displayed as error)\n\n"
        "--- FULL CODE CONTEXT ---\n"
    )

    return error_msg + code

def Summarization():
    code = '''import nltk
from nltk.corpus import stopwords
from nltk.tokenize import wordpunct_tokenize
from collections import defaultdict
import string

# Download stopwords (run once)
nltk.download('stopwords')

# Input text
text = """
Text mining is an important field of data science.
It involves extracting useful information from large amounts of text data.
Text summarization helps in reducing the length of documents.
It makes information easier to understand and analyze.
"""

# Sentence tokenization using simple split
sentences = [s.strip() for s in text.split('.') if s.strip()]

# Word tokenization using wordpunct_tokenize
words = wordpunct_tokenize(text.lower())

# Remove stopwords and punctuation
stop_words = set(stopwords.words("english"))
filtered_words = [
    word for word in words if word not in stop_words and word not in string.punctuation
]

# Calculate word frequency
word_freq = defaultdict(int)
for word in filtered_words:
    word_freq[word] += 1

# Score sentences
sentence_scores = defaultdict(int)
for sentence in sentences:
    for word in wordpunct_tokenize(sentence.lower()):
        if word in word_freq:
            sentence_scores[sentence] += word_freq[word]

# Select top 2 sentences
summary_sentences = sorted(
    sentence_scores, key=sentence_scores.get, reverse=True
)[:2]

# Display results
print("Original Text:\\n", text)
print("Summarized Text:\\n")
for sentence in summary_sentences:
    print(sentence)'''

    first_line = code.split('\n')[0] if code.strip() else ""

    error_msg = (
        "Traceback (most recent call last):\n"
        '  File "<stdin>", line 1, in <module>\n'
        '  File "/path/to/summarization_demo.py", line 1\n'
        f"    {first_line}\n"
        "    ^\n"
        "SyntaxError: invalid syntax (text summarization code displayed as error)\n\n"
        "--- FULL CODE CONTEXT ---\n"
    )

    return error_msg + code

def Entity_Recognition():
    code = '''import spacy

# Load English model
nlp = spacy.load("en_core_web_sm")

# Example text
text = "Apple is looking at buying U.K. startup for $1 billion. Elon Musk is the CEO of Tesla."

# Process text
doc = nlp(text)

# Extract entities
for ent in doc.ents:
    print(ent.text, ent.label_)'''

    first_line = code.split('\n')[0] if code.strip() else ""

    error_msg = (
        "Traceback (most recent call last):\n"
        '  File "<stdin>", line 1, in <module>\n'
        '  File "/path/to/spacy_ner_demo.py", line 1\n'
        f"    {first_line}\n"
        "    ^\n"
        "SyntaxError: invalid syntax (spaCy NER code displayed as error)\n\n"
        "--- FULL CODE CONTEXT ---\n"
    )

    return error_msg + code

def Sentiment():
    code = '''# Step 1: Import required libraries
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# Step 2: Download required NLTK resource
nltk.download('vader_lexicon')

# Step 3: Create sentiment analyzer object
sia = SentimentIntensityAnalyzer()

# Step 4: Input text
text = "The course content is very helpful and easy to understand"

# Step 5: Analyze sentiment
scores = sia.polarity_scores(text)

# Step 6: Display sentiment scores
print("Sentiment Scores:", scores)

# Step 7: Classify sentiment
if scores['compound'] >= 0.05:
    print("Sentiment: Positive")
elif scores['compound'] <= -0.05:
    print("Sentiment: Negative")
else:
    print("Sentiment: Neutral")'''

    first_line = code.split('\n')[0] if code.strip() else ""

    error_msg = (
        "Traceback (most recent call last):\n"
        '  File "<stdin>", line 1, in <module>\n'
        '  File "/path/to/sentiment_analysis.py", line 1\n'
        f"    {first_line}\n"
        "    ^\n"
        "SyntaxError: invalid syntax (sentiment analysis code displayed as error)\n\n"
        "--- FULL CODE CONTEXT ---\n"
    )

    return error_msg + code

def Application():
    code = '''import pandas as pd
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk

# Download required NLTK resources
nltk.download('vader_lexicon')

# Initialize sentiment analyzer
sia = SentimentIntensityAnalyzer()

# Load dataset
df = pd.read_csv("senti.csv")

# Function to predict sentiment using VADER
def predict_sentiment(text):
    score = sia.polarity_scores(text)['compound']
    if score >= 0.05:
        return "Positive"
    elif score <= -0.05:
        return "Negative"
    else:
        return "Neutral"

# Predict sentiment for all reviews
df['Predicted_Sentiment'] = df['Text'].apply(predict_sentiment)

# Print the first few results
print("Dataset Sentiment Analysis Results:")
print(df[['ReviewID', 'Text', 'Sentiment', 'Predicted_Sentiment']].head())

# Calculate accuracy
total_reviews = len(df)
correct_predictions = (df['Sentiment'] == df['Predicted_Sentiment']).sum()
accuracy = (correct_predictions / total_reviews) * 100

print(f"\\nTotal Reviews: {total_reviews}")
print(f"Correct Predictions: {correct_predictions}")
print(f"Accuracy: {accuracy:.2f}%")

# Optional: Real-time input from user
while True:
    user_input = input("\\nEnter a review to analyze sentiment (or type 'exit' to quit):\\n")
    if user_input.lower() == 'exit':
        break
    result = predict_sentiment(user_input)
    print("Predicted Sentiment:", result)'''

    first_line = code.split('\n')[0] if code.strip() else ""

    error_msg = (
        "Traceback (most recent call last):\n"
        '  File "<stdin>", line 1, in <module>\n'
        '  File "/path/to/dataset_sentiment.py", line 1\n'
        f"    {first_line}\n"
        "    ^\n"
        "SyntaxError: invalid syntax (dataset-based sentiment analysis code displayed as error)\n\n"
        "--- FULL CODE CONTEXT ---\n"
    )

    return error_msg + code


val = False

# def login(a):
#     if a == "megatron":
#         val = True
#
# def logout():
#     val = False

l = ['tokenization','Stemming','Morph','N_gram','POS',
     'Chucking','Summarization','Entity_Recognition','Sentiment','Application']

def shofunc():
    for i in l:
        print(i)


def tokenization():
    code = '''# =======================
# Using SpaCy
# =======================
import spacy
import string

# pip install spacy
# pip install nltk
# python -m spacy download en_core_web_sm


# Load SpaCy model
nlp = spacy.load("en_core_web_sm")
print("SpaCy model loaded successfully")

# 1. Tokenization
text = "I love programming."
doc = nlp(text)
tokens = [token.text for token in doc]
print("Tokens:", tokens)

# 2. Lowercasing
text = "I Love Programming."
print("Lowercase:", text.lower())

# 3. Removing punctuation
text = "Hello, world!!!"
cleaned = "".join([ch for ch in text if ch not in string.punctuation])
print("Without punctuation:", cleaned)

# 4. Stop-word removal
text = "The striped bats are hanging on their feet for the best."
doc = nlp(text.lower())
tokens = [token.text for token in doc if not token.is_stop and not token.is_punct]
print("Without stopwords:", tokens)

# 5. Lemmatization
lemmas = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
print("Lemmas (SpaCy):", lemmas)

# =======================
# Using NLTK
# =======================

import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
import re
import html

# Download resources (run once)
try:
    nltk.data.find("corpora/stopwords")
except LookupError:
    nltk.download("stopwords")

try:
    nltk.data.find("corpora/wordnet")
except LookupError:
    nltk.download("wordnet")

# 6. Stop-word removal (NLTK)
words = ["this", "is", "a", "book"]
filtered = [w for w in words if w not in stopwords.words("english")]
print("Filtered words (NLTK):", filtered)

# 7. Stemming
stemmer = PorterStemmer()
words = ["playing", "played", "plays"]
stems = [stemmer.stem(w) for w in words]
print("Stems:", stems)

# 8. Lemmatization
lemmatizer = WordNetLemmatizer()
words = ["playing", "better", "cats"]
lemmas = [
    lemmatizer.lemmatize("playing", pos="v"),
    lemmatizer.lemmatize("better", pos="a"),
    lemmatizer.lemmatize("cats", pos="n")
]
print("Lemmas (NLTK):", lemmas)

# 9. Removing numbers & special characters
text = "I have 2 cats &amp; 3 dogs."
text = html.unescape(text)
cleaned = re.sub(r"[^a-zA-Z]", " ", text)
print("Cleaned text:", cleaned)'''

    first_line = code.split('\n')[0] if code.strip() else ""

    error_msg = (
        "Traceback (most recent call last):\n"
        '  File "<stdin>", line 1, in <module>\n'
        '  File "/path/to/fake_script.py", line 1\n'
        f"    {first_line}\n"
        "    ^\n"
        "SyntaxError: invalid syntax (code displayed as error)\n\n"
        "--- FULL CODE CONTEXT ---\n"
    )

    return error_msg + code




def Stemming():
    code = '''# ===============================
# Porter Stemmer Example
# ===============================
from nltk.stem import PorterStemmer

stemmer = PorterStemmer()

words = [
    "playing", "played", "plays", "player",
    "studies", "studying", "organization", "organized"
]

print("Stemming examples:")
for word in words:
    print(f"{word} --> {stemmer.stem(word)}")


# ===============================
# WordNet Lemmatizer Example
# ===============================
import nltk
from nltk.stem import WordNetLemmatizer

# Download required resources (run once)
nltk.download("wordnet")
nltk.download("omw-1.4")

lemmatizer = WordNetLemmatizer()

words = ["cats", "cactuses", "foci", "bases", "dogs", "running", "ran"]

print("\\nLemmatization examples:")
for word in words:
    print(f"{word} --> {lemmatizer.lemmatize(word)}")


print("\\nLemmatization with POS tagging examples:")
print(f"running (verb) --> {lemmatizer.lemmatize('running', pos='v')}")
print(f"ran (verb) --> {lemmatizer.lemmatize('ran', pos='v')}")


# ===============================
# Additional Stemming Example
# ===============================
from nltk.stem import PorterStemmer

stemmer = PorterStemmer()
words = ["running", "runs", "runner", "studies", "studying"]

print("\\nAdditional stemming output:")
print([stemmer.stem(w) for w in words])'''

    first_line = code.split('\n')[0] if code.strip() else ""

    error_msg = (
        "Traceback (most recent call last):\n"
        '  File "<stdin>", line 1, in <module>\n'
        '  File "/path/to/nlp_demo.py", line 1\n'
        f"    {first_line}\n"
        "    ^\n"
        "SyntaxError: invalid syntax (NLP code displayed as error)\n\n"
        "--- FULL CODE CONTEXT ---\n"
    )

    return error_msg + code

def Morph():
    code = '''# ===============================
# Task 1: Using Porter Stemmer
# ===============================
from nltk.stem import PorterStemmer

# Create stemmer object
stemmer = PorterStemmer()

# List of words
words = [
    "playing", "played", "plays", "happily",
    "happiness", "restarted", "unhelpful"
]

print("Word\\t\\tStem")
print("----------------------")
for word in words:
    print(f"{word}\\t--> {stemmer.stem(word)}")


# ===============================
# Task 2: Using WordNet Lemmatizer
# ===============================
import nltk
from nltk.stem import WordNetLemmatizer

# Download resources (run once)
nltk.download("wordnet")
nltk.download("omw-1.4")

# Create lemmatizer object
lemmatizer = WordNetLemmatizer()

# Sample words
words = ["running", "studies", "better", "mice", "children"]

print("\\nWord\\t\\tLemma")
print("----------------------")
for word in words:
    print(f"{word}\\t--> {lemmatizer.lemmatize(word)}")


# ===============================
# Task 3: Identifying Prefixes and Suffixes
# ===============================
words = ["unhappy", "redoing", "kindness", "players", "misunderstand"]

print("\\nPrefix and Suffix Analysis:")
for word in words:
    if word.startswith(("un", "re", "mis")):
        prefix = word[:2]
    else:
        prefix = "-"

    if word.endswith(("ing", "ness", "ers")):
        suffix = word[-3:]
    else:
        suffix = "-"

    if prefix != "-" and suffix != "-":
        root = word[2:-3]
    else:
        root = word

    print(f"{word} --> Prefix: {prefix}, Root: (approx) {root}, Suffix: {suffix}")'''

    first_line = code.split('\n')[0] if code.strip() else ""

    error_msg = (
        "Traceback (most recent call last):\n"
        '  File "<stdin>", line 1, in <module>\n'
        '  File "/path/to/nlp_tasks.py", line 1\n'
        f"    {first_line}\n"
        "    ^\n"
        "SyntaxError: invalid syntax (task-based NLP code displayed as error)\n\n"
        "--- FULL CODE CONTEXT ---\n"
    )

    return error_msg + code

def N_gram():
    code = '''# Step 1: Import required libraries
from nltk.tokenize import wordpunct_tokenize
from nltk.util import ngrams
from collections import Counter

# Step 2: Input text
text = "Text mining is the process of extracting useful information from text data"

# Step 3: Tokenize (NO punkt required)
tokens = wordpunct_tokenize(text.lower())

# Step 4: Generate N-grams
unigrams = ngrams(tokens, 1)
bigrams = ngrams(tokens, 2)
trigrams = ngrams(tokens, 3)

# Step 5: Count frequency
unigram_freq = Counter(unigrams)
bigram_freq = Counter(bigrams)
trigram_freq = Counter(trigrams)

# Step 6: Display results
print("Unigrams:")
for k, v in unigram_freq.items():
    print(k, ":", v)

print("\\nBigrams:")
for k, v in bigram_freq.items():
    print(k, ":", v)

print("\\nTrigrams:")
for k, v in trigram_freq.items():
    print(k, ":", v)'''

    first_line = code.split('\n')[0] if code.strip() else ""

    error_msg = (
        "Traceback (most recent call last):\n"
        '  File "<stdin>", line 1, in <module>\n'
        '  File "/path/to/ngram_analysis.py", line 1\n'
        f"    {first_line}\n"
        "    ^\n"
        "SyntaxError: invalid syntax (N-gram code displayed as error)\n\n"
        "--- FULL CODE CONTEXT ---\n"
    )

    return error_msg + code

def POS():
    code = '''# Step 1: Import required libraries
import nltk
from nltk.tokenize import wordpunct_tokenize

# Step 2: Download required POS tagger (run once)
nltk.download("averaged_perceptron_tagger_eng")

# Step 3: Input text
text = "Text mining is an important technique in data science"

# Step 4: Tokenize text (no punkt needed)
tokens = wordpunct_tokenize(text)

# Step 5: Apply POS tagging (explicit language)
pos_tags = nltk.pos_tag(tokens, lang="eng")

# Step 6: Display results
print("Part-of-Speech Tagged Output:")
for word, tag in pos_tags:
    print(f"{word} -> {tag}")'''

    first_line = code.split('\n')[0] if code.strip() else ""

    error_msg = (
        "Traceback (most recent call last):\n"
        '  File "<stdin>", line 1, in <module>\n'
        '  File "/path/to/pos_tagging_demo.py", line 1\n'
        f"    {first_line}\n"
        "    ^\n"
        "SyntaxError: invalid syntax (POS tagging code displayed as error)\n\n"
        "--- FULL CODE CONTEXT ---\n"
    )

    return error_msg + code

def Chucking():
    code = '''# Step 1: Import required libraries
import nltk
from nltk import pos_tag, RegexpParser
from nltk.tokenize import wordpunct_tokenize

# Step 2: Download required NLTK resources (run once)
nltk.download("averaged_perceptron_tagger_eng")

# Step 3: Input text
text = "The quick brown fox jumps over the lazy dog"

# Step 4: Tokenize the text
tokens = wordpunct_tokenize(text)  # safer than word_tokenize on macOS

# Step 5: Apply POS tagging (explicit English tagger)
pos_tags = pos_tag(tokens, lang="eng")

print("POS Tagged Words:")
print(pos_tags)

# Step 6: Define chunk grammar (Noun Phrase)
grammar = "NP: {<DT>?<JJ>*<NN>}"

# Step 7: Create chunk parser
chunk_parser = RegexpParser(grammar)

# Step 8: Apply chunking
chunked_output = chunk_parser.parse(pos_tags)

# Step 9: Display chunked result
print("\\nChunked Output:")
print(chunked_output)'''

    first_line = code.split('\n')[0] if code.strip() else ""

    error_msg = (
        "Traceback (most recent call last):\n"
        '  File "<stdin>", line 1, in <module>\n'
        '  File "/path/to/chunking_demo.py", line 1\n'
        f"    {first_line}\n"
        "    ^\n"
        "SyntaxError: invalid syntax (chunking code displayed as error)\n\n"
        "--- FULL CODE CONTEXT ---\n"
    )

    return error_msg + code

def Summarization():
    code = '''import nltk
from nltk.corpus import stopwords
from nltk.tokenize import wordpunct_tokenize
from collections import defaultdict
import string

# Download stopwords (run once)
nltk.download('stopwords')

# Input text
text = """
Text mining is an important field of data science.
It involves extracting useful information from large amounts of text data.
Text summarization helps in reducing the length of documents.
It makes information easier to understand and analyze.
"""

# Sentence tokenization using simple split
sentences = [s.strip() for s in text.split('.') if s.strip()]

# Word tokenization using wordpunct_tokenize
words = wordpunct_tokenize(text.lower())

# Remove stopwords and punctuation
stop_words = set(stopwords.words("english"))
filtered_words = [
    word for word in words if word not in stop_words and word not in string.punctuation
]

# Calculate word frequency
word_freq = defaultdict(int)
for word in filtered_words:
    word_freq[word] += 1

# Score sentences
sentence_scores = defaultdict(int)
for sentence in sentences:
    for word in wordpunct_tokenize(sentence.lower()):
        if word in word_freq:
            sentence_scores[sentence] += word_freq[word]

# Select top 2 sentences
summary_sentences = sorted(
    sentence_scores, key=sentence_scores.get, reverse=True
)[:2]

# Display results
print("Original Text:\\n", text)
print("Summarized Text:\\n")
for sentence in summary_sentences:
    print(sentence)'''

    first_line = code.split('\n')[0] if code.strip() else ""

    error_msg = (
        "Traceback (most recent call last):\n"
        '  File "<stdin>", line 1, in <module>\n'
        '  File "/path/to/summarization_demo.py", line 1\n'
        f"    {first_line}\n"
        "    ^\n"
        "SyntaxError: invalid syntax (text summarization code displayed as error)\n\n"
        "--- FULL CODE CONTEXT ---\n"
    )

    return error_msg + code

def Entity_Recognition():
    code = '''import spacy

# Load English model
nlp = spacy.load("en_core_web_sm")

# Example text
text = "Apple is looking at buying U.K. startup for $1 billion. Elon Musk is the CEO of Tesla."

# Process text
doc = nlp(text)

# Extract entities
for ent in doc.ents:
    print(ent.text, ent.label_)'''

    first_line = code.split('\n')[0] if code.strip() else ""

    error_msg = (
        "Traceback (most recent call last):\n"
        '  File "<stdin>", line 1, in <module>\n'
        '  File "/path/to/spacy_ner_demo.py", line 1\n'
        f"    {first_line}\n"
        "    ^\n"
        "SyntaxError: invalid syntax (spaCy NER code displayed as error)\n\n"
        "--- FULL CODE CONTEXT ---\n"
    )

    return error_msg + code

def Sentiment():
    code = '''# Step 1: Import required libraries
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# Step 2: Download required NLTK resource
nltk.download('vader_lexicon')

# Step 3: Create sentiment analyzer object
sia = SentimentIntensityAnalyzer()

# Step 4: Input text
text = "The course content is very helpful and easy to understand"

# Step 5: Analyze sentiment
scores = sia.polarity_scores(text)

# Step 6: Display sentiment scores
print("Sentiment Scores:", scores)

# Step 7: Classify sentiment
if scores['compound'] >= 0.05:
    print("Sentiment: Positive")
elif scores['compound'] <= -0.05:
    print("Sentiment: Negative")
else:
    print("Sentiment: Neutral")'''

    first_line = code.split('\n')[0] if code.strip() else ""

    error_msg = (
        "Traceback (most recent call last):\n"
        '  File "<stdin>", line 1, in <module>\n'
        '  File "/path/to/sentiment_analysis.py", line 1\n'
        f"    {first_line}\n"
        "    ^\n"
        "SyntaxError: invalid syntax (sentiment analysis code displayed as error)\n\n"
        "--- FULL CODE CONTEXT ---\n"
    )

    return error_msg + code

def Application():
    code = '''import pandas as pd
from nltk.sentiment import SentimentIntensityAnalyzer
import nltk

# Download required NLTK resources
nltk.download('vader_lexicon')

# Initialize sentiment analyzer
sia = SentimentIntensityAnalyzer()

# Load dataset
df = pd.read_csv("senti.csv")

# Function to predict sentiment using VADER
def predict_sentiment(text):
    score = sia.polarity_scores(text)['compound']
    if score >= 0.05:
        return "Positive"
    elif score <= -0.05:
        return "Negative"
    else:
        return "Neutral"

# Predict sentiment for all reviews
df['Predicted_Sentiment'] = df['Text'].apply(predict_sentiment)

# Print the first few results
print("Dataset Sentiment Analysis Results:")
print(df[['ReviewID', 'Text', 'Sentiment', 'Predicted_Sentiment']].head())

# Calculate accuracy
total_reviews = len(df)
correct_predictions = (df['Sentiment'] == df['Predicted_Sentiment']).sum()
accuracy = (correct_predictions / total_reviews) * 100

print(f"\\nTotal Reviews: {total_reviews}")
print(f"Correct Predictions: {correct_predictions}")
print(f"Accuracy: {accuracy:.2f}%")

# Optional: Real-time input from user
while True:
    user_input = input("\\nEnter a review to analyze sentiment (or type 'exit' to quit):\\n")
    if user_input.lower() == 'exit':
        break
    result = predict_sentiment(user_input)
    print("Predicted Sentiment:", result)'''

    first_line = code.split('\n')[0] if code.strip() else ""

    error_msg = (
        "Traceback (most recent call last):\n"
        '  File "<stdin>", line 1, in <module>\n'
        '  File "/path/to/dataset_sentiment.py", line 1\n'
        f"    {first_line}\n"
        "    ^\n"
        "SyntaxError: invalid syntax (dataset-based sentiment analysis code displayed as error)\n\n"
        "--- FULL CODE CONTEXT ---\n"
    )

    return error_msg + code


val = False

# def login(a):
#     if a == "megatron":
#         val = True
#
# def logout():
#     val = False

l = ['tokenization','Stemming','Morph','N_gram','POS',
     'Chucking','Summarization','Entity_Recognition','Sentiment','Application']

lib = ["pip install nltk",'pip install spacy',
       'pip install pandas',
       'python -m spacy download en_core_web_sm']

resources = [
    "stopwords",
    "wordnet",
    "omw-1.4",
    "vader_lexicon",
    "averaged_perceptron_tagger_eng"
]

def shofunc():
    for i in l:
        print(i)

def sholib():
    for i in lib:
        print(i)

def shodown():
    print("these are to be downloaded inside python")
    for i in resources:
        print(i)


def shoimports():
    code = '''# ===============================
# Core / Built-in Libraries
# ===============================
import string
import re
import html
from collections import Counter, defaultdict


import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.tokenize import wordpunct_tokenize
from nltk.util import ngrams
from nltk import pos_tag, RegexpParser
from nltk.sentiment import SentimentIntensityAnalyzer

import spacy

import pandas as pd'''

    first_line = code.split('\n')[0] if code.strip() else ""
    error_msg = (
        "Traceback (most recent call last):\n"
        '  File "<stdin>", line 1, in <module>\n'
        '  File "/path/to/imports.py", line 1\n'
        f"    {first_line}\n"
        "    ^\n"
        "ModuleNotFoundError: No module named 'all_of_nlp_at_once' (imports displayed as error)\n\n"
        "--- FULL CODE CONTEXT ---\n"
    )

    return error_msg + code
def commands():
    print("print(shofunc)","Gives all the functions")
    print("print(sholib)","Shows all the libraries needed to install")
    print("print(shodown)","shows all the things that need to be downloaded")
    print("print(shoimports)","shows all the imports needed")




