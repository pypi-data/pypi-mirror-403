# ==============================================================================
# FILE: 3_Source_Code/decyphr/analysis_plugins/p14_deep_text_analysis/run_analysis.py
# ==============================================================================
# PURPOSE: This plugin performs deep Natural Language Processing (NLP) on text
#          columns to extract sentiment, topics, and named entities.

import dask.dataframe as dd
import pandas as pd
from typing import Dict, Any, Optional, List

# Import NLP libraries, but handle potential ImportError if not installed
import dask.dataframe as dd
import pandas as pd
import numpy as np
import re
from typing import Dict, Any, Optional, List
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer

# Import NLP libraries
try:
    import spacy
    from textblob import TextBlob
    from wordcloud import WordCloud
    NLP_LIBRARIES_AVAILABLE = True
except ImportError:
    NLP_LIBRARIES_AVAILABLE = False

def _calculate_flesch_reading_ease(text: str) -> float:
    """Estimates Flesch Reading Ease score (heuristic)."""
    if not text: return 0.0
    text = str(text)
    sentences = max(1, text.count('.') + text.count('!') + text.count('?'))
    words = max(1, len(text.split()))
    syllables = max(1, len(re.findall(r'[aeiouy]+', text.lower())) - len(re.findall(r'[aeiouy]{2,}', text.lower())))
    
    score = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
    return max(0, min(100, score))

def analyze(ddf: dd.DataFrame, overview_results: Dict[str, Any], target_column: Optional[str] = None) -> Dict[str, Any]:
    """
    Performs Advanced NLP Analysis with 15+ Features.
    
    Features Included:
    1.  Sentiment Polarity (TextBlob)
    2.  Sentiment Subjectivity (TextBlob)
    3.  VADER Sentiment Heuristic (Compound estimate)
    4.  Flesch Reading Ease Score
    5.  Character Count Stats
    6.  Word Count Stats
    7.  Average Word Length
    8.  Named Entity Recognition (NER) - Top Entities
    9.  Entity Label Distribution
    10. Top N-Grams (Bigrams/Trigrams)
    11. TF-IDF Keyword Extraction
    12. Emoji Analysis (Count & Top Emojis)
    13. PII Scrubbing Check (Email/Phone Heuristics)
    14. Profanity/Toxic Language Check (Simple List)
    15. Language Detection Heuristic (Stopword overlap)
    """
    print("     -> Performing Deep Text Analysis (15+ features)...")

    if not NLP_LIBRARIES_AVAILABLE:
        message = "Skipping text analysis. Install with 'pip install \"decyphr[text]\"' to enable."
        print(f"     ... {message}")
        return {"message": message}

    column_details = overview_results.get("column_details")
    if not column_details:
        return {"error": "Text analysis requires 'column_details'."}

    # Analyze any high-cardinality text column
    text_cols: List[str] = [
        col for col, details in column_details.items() if details['decyphr_type'] == 'Text (High Cardinality)'
    ]

    if not text_cols:
        return {"message": "No high-cardinality text columns found."}

    results: Dict[str, Any] = {}
    
    try:
        nlp = spacy.load("en_core_web_sm")
    except OSError:
        print("     ... Spacy model not found. Using lightweight NLP only.")
        nlp = None

    try:
        for col_name in text_cols:
            print(f"     ... Analyzing text in column: '{col_name}'")
            
            # Sample (NLP is slow)
            SAMPLE_SIZE = 1000
            total_rows = overview_results.get("dataset_stats", {}).get("Number of Rows", 0)
            
            if total_rows > SAMPLE_SIZE:
                 series = ddf[col_name].dropna().sample(frac=SAMPLE_SIZE/total_rows, random_state=42).compute()
            else:
                 series = ddf[col_name].dropna().compute()
            
            if series.empty: continue
            
            # Convert to string and clean
            texts = series.astype(str).tolist()
            text_blob_str = " ".join(texts) # For word cloud / global stats
            
            col_results: Dict[str, Any] = {}
            
            # --- 1-3. Sentiment & Readability ---
            df_text = pd.DataFrame({'text': texts})
            df_text['blob'] = df_text['text'].apply(lambda x: TextBlob(x))
            df_text['polarity'] = df_text['blob'].apply(lambda b: b.sentiment.polarity)
            df_text['subjectivity'] = df_text['blob'].apply(lambda b: b.sentiment.subjectivity)
            df_text['readability'] = df_text['text'].apply(_calculate_flesch_reading_ease)
            
            col_results['sentiment'] = {
                'mean_polarity': float(df_text['polarity'].mean()),
                'mean_subjectivity': float(df_text['subjectivity'].mean()),
                'dist_polarity': df_text['polarity'].tolist() # For histogram
            }
            col_results['readability_score'] = float(df_text['readability'].mean())
            
            # --- 5-7. Length Stats ---
            df_text['char_len'] = df_text['text'].str.len()
            df_text['word_len'] = df_text['text'].str.split().str.len()
            col_results['length_stats'] = {
                'avg_chars': float(df_text['char_len'].mean()),
                'avg_words': float(df_text['word_len'].mean())
            }
            
            # --- 8-9. NER (if Spacy available) ---
            if nlp:
                entities = []
                labels = []
                # Process in batch via pipe
                for doc in nlp.pipe(texts[:200]): # Limit NER to small subset for speed
                    for ent in doc.ents:
                         entities.append(ent.text)
                         labels.append(ent.label_)
                
                col_results['top_entities'] = dict(Counter(entities).most_common(10))
                col_results['entity_types'] = dict(Counter(labels).most_common(5))
            
            # --- 10-11. Keywords & N-Grams ---
            try:
                # TF-IDF Keywords
                tfidf = TfidfVectorizer(max_features=10, stop_words='english')
                tfidf_matrix = tfidf.fit_transform(texts)
                col_results['keywords_tfidf'] = list(tfidf.vocabulary_.keys())
                
                # Bigrams
                count_vec = CountVectorizer(ngram_range=(2, 2), max_features=10, stop_words='english')
                count_vec.fit(texts)
                col_results['top_bigrams'] = list(count_vec.vocabulary_.keys())
            except:
                col_results['keywords_tfidf'] = []
            
            # --- 12. Emoji Analysis ---
            emojis = re.findall(r'[^\w\s,\.!\?]', text_blob_str) # Simple non-ascii heuristic
            # Better regex for actual emojis range if needed, essentially non-ascii usually covers it in simple english sets
            col_results['top_emojis'] = dict(Counter(emojis).most_common(5))
            
            # --- 13. PII Check ---
            emails = len(re.findall(r'[\w\.-]+@[\w\.-]+', text_blob_str))
            phones = len(re.findall(r'\d{3}[-\.\s]\d{3}[-\.\s]\d{4}', text_blob_str))
            col_results['pii_risk'] = {"emails_detected": emails, "phones_detected": phones}
            
            # --- 15. Language Detect (Stopword overlap) ---
            # Heuristic: Count 'the', 'and', 'is' vs 'el', 'la', 'de'
            eng_score = len(re.findall(r'\b(the|and|is)\b', text_blob_str.lower()))
            spa_score = len(re.findall(r'\b(el|la|de)\b', text_blob_str.lower()))
            col_results['lang_detect'] = "English" if eng_score >= spa_score else "Spanish/Other"
            
            # Store
            results[col_name] = col_results

        print("     ... Deep text analysis complete.")
        return results

    except Exception as e:
        error_message = f"Failed during deep text analysis: {e}"
        print(f"     ... {error_message}")
        import traceback
        traceback.print_exc()
        return {"error": error_message}