import os
import re
import yaml
import nltk
import pandas as pd
from tqdm import tqdm
from yaml import Loader
from gensim.models import FastText
from nltk import WordNetLemmatizer


class FastTextTrainer:
    def __init__(self, specs_dir, output_model_file):
        self.specs_dir = specs_dir
        self.output_model_file = output_model_file
        self.model = None

    def get_nl(self, search_dict):
        """
        Takes a dict with nested lists and dicts,
        and searches all dicts for a key of the "description" and "summary" field.
        """
        fields_found = []

        for key, value in search_dict.items():

            if key == "description":
                fields_found.append(value)
            elif key == "summary":
                fields_found.append(value)
            elif isinstance(value, dict):
                results = self.get_nl(value)
                for result in results:
                    fields_found.append(result)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        more_results = self.get_nl(item)
                        for another_result in more_results:
                            fields_found.append(another_result)

        return fields_found

    def preprocess_text(self, document):
        stemmer = WordNetLemmatizer()
        en_stop = set(nltk.corpus.stopwords.words('english'))

        # Remove extra white space from text
        document = re.sub(r'\s+', ' ', document, flags=re.I)

        # Remove all the special characters from text
        document = re.sub(r'\W', ' ', str(document))

        # Remove all single characters from text
        document = re.sub(r'\s+[a-zA-Z]\s+', ' ', document)

        # Converting to Lowercase
        document = document.lower()

        # Word tokenization
        tokens = document.split()
        lemma_txt = [stemmer.lemmatize(word) for word in tokens]
        lemma_no_stop_txt = [word for word in lemma_txt if word not in en_stop]

        clean_txt = ' '.join(lemma_no_stop_txt)

        return clean_txt

    def train_model(self):
        swaggers = [os.path.join(dp, f) for dp, dn, filenames in os.walk(self.specs_dir) for f in filenames]
        total_swagger = len(swaggers)
        total_processed = 0

        num_swagger = 0
        num_nl = 0
        no_nl = 0
        result = ""
        for swagger in swaggers:
            print(swagger + " is processing...")
            total_processed = total_processed + 1
            with open(swagger) as f:
                try:
                    data = yaml.load(f, Loader=Loader)
                    num_swagger = num_swagger + 1

                    nls = self.get_nl(data)
                    if not nls:
                        no_nl = no_nl + 1
                        print("No NL!")
                        continue
                    for nl in nls:
                        if isinstance(nl, str):
                            processed_nl = self.preprocess_text(nl)
                            if len(processed_nl) > 3:
                                result = result + "{\"text\": \"" + processed_nl + "\"}\n"
                                num_nl = num_nl + 1

                    if num_swagger % 200 == 0:
                        print("Processed " + str(total_processed) + " out of " + str(total_swagger) + '.')
                        print("Saved!")
                        with open("nl.json", 'w') as fnl:
                            fnl.write(result)

                except Exception as msg:
                    print(msg)

        print(str(total_processed) + " number of specifications are processed.")
        print(str(num_nl) + " number of descriptions are processed.")

        with open("nl.json", 'w') as fnl:
            fnl.write(result)

        rest_df = pd.read_json("nl.json", lines=True)
        all_sent = list(rest_df['text'])

        word_tokenizer = nltk.WordPunctTokenizer()
        word_tokens = [word_tokenizer.tokenize(sent) for sent in tqdm(all_sent)]

        # Defining values for parameters
        window_size = 3
        min_word = 3
        down_sampling = 1e-2

        fasttext_model = FastText(word_tokens,
                                  window=window_size,
                                  min_count=min_word,
                                  sample=down_sampling,
                                  workers=4,
                                  sg=1)

        fasttext_model.save(self.output_model_file)
        self.model = fasttext_model
