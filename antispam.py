#!/usr/bin/env python3

from __future__ import print_function, division
import os
import random
import sys
import re
import argparse
import eml_parser
from enum import Enum
from nltk import word_tokenize, WordNetLemmatizer
from nltk.corpus import stopwords
from nltk import NaiveBayesClassifier, classify
from sklearn.externals import joblib
from bs4 import BeautifulSoup

from common_spam_words import common_spam_words_en, common_spam_words_cz, forbidden_words
from spam_signs import SpamSigns
from html_tag_list import html_tag_list

list_of_spam_signs = []

# nltk.download('stopwords')
# nltk.download('punkt')
# nltk.download('wordnet')


stoplist = stopwords.words('english')


# enum of possible results
class ResultTypes(Enum):
    OK = 1
    SPAM = 2
    FAIL = 3



def create_and_train_classifier():
    # initialise the data
    spam = init_lists('Tests/aaa/spam/')
    spam += init_lists('Tests/enron3/spam/')
    ham = init_lists('Tests/aaa/ham/')
    ham += init_lists('Tests/enron3/ham/')
    all_emails = [(email, 'spam') for email in spam]
    all_emails += [(email, 'ham') for email in ham]
    random.shuffle(all_emails)

    # extract the features
    all_features = [(get_features(email), label) for (email, label) in all_emails]

    # train the classifier
    classifier = NaiveBayesClassifier.train(all_features)
    joblib.dump(classifier, 'classifier')
    sys.exit(0)


# print result of an e-mail
def print_result(result_value):
    if result_value == ResultTypes.OK:
        print(" - OK")
    elif result_value == ResultTypes.SPAM:
        print(" - SPAM - " + str(list_of_spam_signs))
    elif result_value == ResultTypes.FAIL:
        print(" - FAIL - failed to open e-mail file")


def init_lists(folder):
    a_list = []
    file_list = os.listdir(folder)
    for a_file in file_list:
        f = open(folder + a_file, 'rb')
        a_list.append(f.read())
    f.close()
    return a_list


def preprocess(sentence):
    lemmatizer = WordNetLemmatizer()
    return [lemmatizer.lemmatize(word.lower()) for word in word_tokenize(str(sentence, errors='ignore'))]


def get_features(text):
    return {word: True for word in preprocess(text) if not word in stoplist}



def is_body_empty(parsed_email):
    if 'body' not in parsed_email or len(parsed_email['body']) == 0 or 'content' not in parsed_email['body'][0]:
        return True

    return False



def get_sender_recipient_subject(parsed_email):
    sender = None
    recipient = None
    subject = None

    if 'header' in parsed_email:
        if 'from' in parsed_email['header']:
            sender = parsed_email['header']['from']

        if 'subject' in parsed_email['header']:
            subject = parsed_email['header']['subject']

        if 'to' in parsed_email['header']:
            recipient = parsed_email['header']['to']

        # if 'date' in parsed_email['header']:
            # sys.stderr.write(str(parsed_email['header']['date']) + '\n')

        # if 'received' in parsed_email['header']:
        #     sys.stderr.write(str(parsed_email['header']['received']) + '\n')

    return (sender, recipient, subject)



def too_many_empty_lines(email_body, value):
    empty_lines_count = 0
    email_lines = email_body.split('\n')

    if len(email_lines) == 0 or email_body == '' or email_body.isspace():
        return 0

    for line in email_lines:
        if line.isspace() or line == '':
            empty_lines_count += 1

    if float(empty_lines_count / len(email_lines)) * 100.0 > 25:
        return float(empty_lines_count / len(email_lines)) * 100.0 * 2 * value

    return 0



def remove_html(email_content):
    soup = BeautifulSoup(email_content, "html.parser")

    for script in soup(["script", "style"]):
        script.extract()

    email_content = soup.get_text()
    words_in_email = re.findall(r"[\w']+", email_content)

    if len(words_in_email) == 0:
        return 1
    else:
        return len(words_in_email)



def get_bad_word_content_score(email_content, value):
    global list_of_spam_signs
    bad_word_count = 0
    words_in_content = re.findall(r"[\w']+", email_content)

    if len(words_in_content) == 0:
        return 0

    # email_body = email_body.replace('\'', '\'')
    # for word in words_in_content:
    #     if word in common_spam_words_en + common_spam_words_cz:
    #         bad_word_count += 1
    #         list_of_spam_signs.append("CONTAINS: " + word)

    #     elif word in forbidden_words:
    #         bad_word_count += 10
    #         list_of_spam_signs.append("CONTAINS: " + word)

    for bad_word in common_spam_words_en + common_spam_words_cz:
        occurences = re.findall(r'\s' + bad_word.replace(' ', '\s*') + r'\s', email_content)
        if occurences != []:
            bad_word_count += len(occurences)
            # bad_word_count += email_content.count(bad_word)
            list_of_spam_signs.append("CONTAINS: " + bad_word)
            # sys.stderr.write(str(bad_word) + " ")

    for forbidden_word in forbidden_words:
        occurences = re.findall(r'\s' + forbidden_word.replace(' ', '\s*') + r'\s', email_content)
        if occurences != []:
            bad_word_count += len(occurences) * 10
            # bad_word_count += email_content.count(forbidden_word) * 10
            list_of_spam_signs.append("CONTAINS: " + forbidden_word)

    # for bad_word in common_spam_words_en + common_spam_words_cz:
    #     if bad_word in email_body:
    #         # r = re.compile(r'[^a-zA-Z]' + bad_word + r'[^a-zA-Z]')
    #         # bad_word_count += len(re.findall(r + bad_word + r, email_body))
    #         # bad_word_count += email_body.count(' ' + bad_word) + email_body.count(bad_word + ' ')
    #         list_of_spam_signs.append("CONTAINS: " + bad_word)

    # for forbidden_word in forbidden_words:
    #     if forbidden_word in email_body:
    #         # bad_word_count += len(re.findall(r'[^a-zA-Z]' + forbidden_word + r'[^a-zA-Z]', email_body)) * 5
    #         # bad_word_count += (email_body.count(' ' + forbidden_word) + email_body.count(forbidden_word + ' ')) * 5
    #         list_of_spam_signs.append("CONTAINS: " + forbidden_word)

    # sys.stderr.write(str(float(bad_word_count / remove_html(email_content)) * 100.0) + '\n')

    score = float(bad_word_count / remove_html(email_content)) * 100.0

    non_ascii_chars = []
    for char in email_content:
        if ord(char) >= 128 and ord(char) not in [225, 205, 237, 269, 271, 233, 283, 328, 243, 345, 353, 357, 250, 367, 366, 253, 382, 193, 268, 270, 201, 282, 327, 211, 344, 352, 356, 218, 221, 381]:
            non_ascii_chars.append(char)

    if len(non_ascii_chars) != 0:
        list_of_spam_signs.append(SpamSigns.NON_ASCII_CHARACTERS.value)

    score += float(len(non_ascii_chars) * 40.0 / remove_html(email_content))

    single_char_count = 0
    for word in words_in_content:
        if len(word) == 1:
            single_char_count += 1

    single_char_ratio = float(single_char_count / remove_html(email_content))
    if single_char_ratio > 0.5:
        score += single_char_ratio * 4
        list_of_spam_signs.append(SpamSigns.MANY_SINGLE_CHARS.value)

    return score * value



def get_html_content_score(email_content, value):
    global list_of_spam_signs
    score = 0.0
    for html_tag in html_tag_list:
        if email_content.count("<" + html_tag) != email_content.count("</" + html_tag):
            list_of_spam_signs.append(SpamSigns.OPEN_HTML_TAG.value)
            score += 0.5
        if "<bgsound" in email_content:
            list_of_spam_signs.append(SpamSigns.BGSOUND_TAG.value)
            score += 1.0

    soup = BeautifulSoup(email_content, "html.parser")
    if len(soup.find_all(b'font')) > 1:
        list_of_spam_signs.append(SpamSigns.MANY_FONTS)
        score += 10 * len(soup.find_all(b'font'))

    return score * value



def get_external_links_score(email_content, value):
    global list_of_spam_signs
    score = 0.0

    external_links = re.findall(r'http[s]?://[a-zA-Z0-9.:/\-~?=&_]*', email_content)
    fishy_external_links = re.findall(r'http[s]?\s+:\s+', email_content)
    score += len(fishy_external_links) * 2 * value

    if external_links == []:
        return score

    if len(external_links) > 10:
        score += float(len(external_links) / 5.0) + 3.0
        list_of_spam_signs.append(SpamSigns.MANY_EXTERNAL_LINKS.value)

    for link in external_links:
        if re.search(r'(\.ru|goo\.gl)', link) != None:
            score += 5.0
            list_of_spam_signs.append("URL CONTAINS: " + str(re.search(r'(\.ru|goo\.gl)', link).group()))

    return score * value



def get_uppercase_score(email_content, value):
    global list_of_spam_signs
    uppercase_word_count = 0
    words_in_content = re.findall(r"[#\w']+", email_content)

    if len(words_in_content) == 0:
        return 0

    for word in words_in_content:
        if word.isupper() and '#' not in word and word.isalpha():
            if word in forbidden_words:
                uppercase_word_count += 10
            elif word in common_spam_words_en + common_spam_words_cz:
                uppercase_word_count += 5
            else:
                uppercase_word_count += 1

    if uppercase_word_count != 0:
        list_of_spam_signs.append(SpamSigns.UPPERCASE_WORDS.value)

    return min(float(uppercase_word_count / float(remove_html(email_content))) * value * 50.0, 15.0)



def get_fishy_characters_score(email_content, value):
    global list_of_spam_signs
    fishy_characters_score = 0

    for fishy_character in ['!', '?', '=']:
        if email_content.count(fishy_character) != 0:
            fishy_characters_score += float(email_content.count(fishy_character) / remove_html(email_content)) * value * 20

    for fishy_character in ['$', '#', '%', '*', '€']:
        if email_content.count(fishy_character) != 0:
            fishy_characters_score += float(email_content.count(fishy_character) / remove_html(email_content)) * value * 40

    if fishy_characters_score > 0.5:
        list_of_spam_signs.append(SpamSigns.MANY_FISHY_CHARACTERS.value)
        return fishy_characters_score

    return 0



def get_content_spam_score(email_content, content_type):
    global list_of_spam_signs
    score = 0.0
    value = 1.5 if content_type == 'subject' else 1.0

    score += get_uppercase_score(email_content, value)
    email_content = email_content.lower()
    score += get_bad_word_content_score(email_content, value)
    score += get_html_content_score(email_content, value)
    score += get_external_links_score(email_content, value)
    score += get_fishy_characters_score(email_content, value)

    if too_many_empty_lines(email_content, value) is True:
        score += list_of_spam_signs.append(SpamSigns.MANY_EMPTY_LINES.value)

    return score


def get_sender_score(sender):
    global list_of_spam_signs
    score = 0.0

    if sender.isspace():
        score += 10.0
    else:
        if '@' not in sender:
            score += 10.0

    if score != 0.0:
        list_of_spam_signs.append(SpamSigns.FISHY_SENDER.value)

    return score


# check e-mail for signs of commonly used spam words
def check_email(email_content):
    global list_of_spam_signs
    score = 0.0

    try:
        parsed_email = eml_parser.eml_parser.decode_email_b(email_content, include_raw_body=True, include_attachment_data=True)
    except:
        print_result(ResultTypes.SPAM)
        return

    # print("\n")
    # print(parsed_email)
    # print("\n")

    (sender, recipient, subject) = get_sender_recipient_subject(parsed_email)
    if recipient == []:
        list_of_spam_signs.append(SpamSigns.RECIPIENT_EMPTY.value)
        score += 10

    if sender is None:
        list_of_spam_signs.append(SpamSigns.MISSING_SENDER.value)
        score += 5
    else:
        score += get_sender_score(sender)

    if subject != None:
        score += get_content_spam_score(subject, 'subject')

    if is_body_empty(parsed_email) or (len(parsed_email['body']) == 1 and parsed_email['body'][0]['content'] == ''):
        list_of_spam_signs.append(SpamSigns.BODY_EMPTY.value)
        score += 20

    else:
        for index in range(len(parsed_email['body'])):
            score += get_content_spam_score(parsed_email['body'][index]['content'], 'body')
        # if 'content_header' not in parsed_email['body'][0] or parsed_email['body'][0]['content_header'] == {}:
        #     list_of_spam_signs.append(SpamSigns.EMPTY_CONTENT_HEADER.value)
        #     score += 5

    if 'attachment' in parsed_email and len(parsed_email['attachment']) > 0:
        list_of_spam_signs.append(SpamSigns.CONTAINS_ATTACHMENT.value)

        for single_attachment in parsed_email['attachment']:
            score += 2
            if 'filename' in single_attachment and '.' not in single_attachment['filename']:
                list_of_spam_signs.append(SpamSigns.FISHY_ATTACHMENT_FILENAME.value)
                score += 5

    # make values distinct
    list_of_spam_signs = list(set(list_of_spam_signs))

    # print_result(ResultTypes.SPAM)
    # print(score)

    if score < 43.0 or len(list_of_spam_signs) < 1:
        print_result(ResultTypes.OK)
    else:
        print_result(ResultTypes.SPAM)
    # TODO set max limits

    return 'spam'



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--train', dest='train', action='store_true',
                        help='train the classifier and exit')
    parser.add_argument('email_filepaths', type=str, nargs='*',
                        help='paths to input e-mails')

    arguments = parser.parse_args()

    if arguments.train:
        create_and_train_classifier()

    # TODO add other classifiers
    classifier = joblib.load('classifier')

    for single_email_path in arguments.email_filepaths:
        del list_of_spam_signs[:]
        print(single_email_path, end='')

        try:
            single_email = open(single_email_path, 'rb')

        except IOError:
            print_result(ResultTypes.FAIL)
            continue

        email_content = single_email.read()
        single_email.close()

        # classify e-mail with the Bayes classifier
        # Bayes_email_class = classifier.classify(get_features(email_content))
        word_check_email_class = check_email(email_content)

        # if Bayes_email_class == word_check_email_class == 'spam':
        #     print_result(ResultTypes.SPAM)

        # elif Bayes_email_class == word_check_email_class == 'ham':
        #     print_result(ResultTypes.OK)

        # else:
        #     if Bayes_email_class == 'ham':
        #         print_result(ResultTypes.OK)

        #     print("NOT SURE - BAYES x WORDS == " + str(Bayes_email_class) + " x " + word_check_email_class)
        #     print_result(ResultTypes.OK)


if __name__ == '__main__':
    main()
