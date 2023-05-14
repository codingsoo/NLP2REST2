import re
import nltk
import yaml
import stanza
from nltk.tree import Tree


def extract_special_format_elements(text):
    """
    Extract various kinds of textual elements enclosed by special characters from the given text.

    This function extracts quoted strings, JSON-like objects, and values
    enumerated in Markdown lists (both hyphen and asterisk types).
    The extracted values are de-duplicated and returned as a list.

    This extraction targets text encased in special characters or formatted in a certain way,
    as a preliminary step before deeper text analysis such as parsing with a constituency tree.

    :param text: The input text from which to extract the textual elements.
    :return: A list of unique extracted textual elements.
    """
    output = (
            re.findall(r'`[^`]*`', text) +
            re.findall(r'"[^"]*"', text) +
            re.findall(r"'[^']*'", text) +
            re.findall(r'\{[^\}]*\}', text)
    )

    if '- ' in text:
        temp_text = text[text.find("- "):]
        temp = re.findall('-[^\n]*\n', temp_text)
        temp.append(temp_text[temp_text.rfind('-'):])
        for t in temp:
            focus_value = t.strip().strip('-').strip().split()[0]
            output.append(focus_value)

    if '* ' in text:
        temp_text = text[text.find("* "):]
        temp = re.findall('\*[^\n]*\n', temp_text)
        temp.append(temp_text[temp_text.rfind('*'):])
        for t in temp:
            focus_value = t.strip().strip('*').strip().split()[0]
            output.append(focus_value)

    for i in reversed(range(len(output))):
        output[i] = output[i].strip()
        if output[i][0] in ["'", '"', '`']:
            output[i] = output[i][1:]
        if output[i][-1] in ["'", '"', '`']:
            output[i] = output[i][:-1]

    return list(set(output))

def find_elements_after_word(tree, target_word, found_word=None, elements=None):
    """
    Find all nouns or numbers that come after a specific word in a constituency parse.
    """
    if found_word is None:
        found_word = [False]
    if elements is None:
        elements = []

    for child in tree:
        if isinstance(child, nltk.Tree):
            if child.label() in ['NN', 'NNS', 'NNP', 'NNPS', 'CD']:
                element = ' '.join(child.leaves())
                if found_word[0]:
                    elements.append(element)
                elif element.lower() == target_word.lower():
                    found_word[0] = True

            find_elements_after_word(child, target_word, found_word, elements)

    return elements





class RuleGenerator:
    def __init__(self, settings_file, fasttext_trainer):
        with open(settings_file, 'r') as file:
            self.settings = yaml.safe_load(file)

        self.fasttext_trainer = fasttext_trainer
        self.nlp = stanza.Pipeline(lang='en', logging_level="FATAL")

    def extract_keywords(self, description, param_names=None):
        """
        Extract keywords from a given description based on the settings.
        """
        if param_names is None:
            param_names = []
        extracted_keywords = {}

        # tokenize the description into sentences
        doc = self.nlp(description)

        for sentence in doc.sentences:
            sentence_text = sentence.text.lower()
            sentence_words = sentence_text.split()
            constituents = None
            special_format = extract_special_format_elements(sentence.text)

            for word in sentence_words:
                highest_score = 0
                selected_keyword = None
                selected_value = None
                selected_keyword_type = None
                selected_params = []
                for keyword_type in self.settings:
                    for keyword in self.settings[keyword_type]:
                        if keyword_type == 'enum':
                            for value in self.settings[keyword_type][keyword]:
                                for term in self.settings[keyword_type][keyword][value]:
                                    similarity = self.fasttext_trainer.model.wv.similarity(word, term)
                                    if similarity > 0.7 and similarity > highest_score:
                                        highest_score = similarity
                                        selected_keyword = keyword
                                        selected_value = value
                                        selected_keyword_type = keyword_type

                        else:
                            for term in self.settings[keyword_type][keyword]:
                                similarity = self.fasttext_trainer.model.wv.similarity(word, term)
                                if similarity > 0.7 and similarity > highest_score:
                                    highest_score = similarity
                                    selected_keyword = keyword
                                    selected_keyword_type = keyword_type
                if selected_value:
                    extracted_keywords[selected_keyword] = selected_value
                elif selected_keyword_type == "value":
                    temp_res = []
                    if special_format:
                        temp_res = special_format
                    else:
                        if not constituents:
                            constituents = Tree.fromstring(str(sentence.constituency))
                        elements = find_elements_after_word(constituents, word)
                        if elements:
                            temp_res = elements

                    if temp_res:
                        if selected_keyword in ["minimum", "maximum", "default"]:
                            for res in temp_res:
                                try:
                                    extracted_keywords[selected_keyword] = int(res.replace(',',''))
                                    break
                                except Exception:
                                    continue
                        elif selected_keyword == "minMax":
                            min_val, max_val = None, None
                            for res in temp_res:
                                try:
                                    val = int(res.replace(',',''))
                                    if min_val is None or val < min_val:
                                        min_val = val
                                    if max_val is None or val > max_val:
                                        max_val = val
                                except Exception:
                                    continue
                            if min_val is not None and max_val is not None:
                                extracted_keywords[selected_keyword] = [min_val, max_val]
                        else:
                            extracted_keywords[selected_keyword] = temp_res
                elif selected_keyword_type == "parameter":
                    for word in sentence_words:
                        for param in param_names:
                            if word == param and param not in selected_params:
                                selected_params.append(param)
                                break
                    if len(selected_params) >= 2:
                        extracted_keywords[selected_keyword] = selected_params

        return extracted_keywords
