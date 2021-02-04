from merriam_webster.api import LearnersDictionary, WordNotFoundException
from googleapiclient.discovery import build
import duckduckgo

api_key = #api_key

def image(query):
    service = build("customsearch", "v1",developerKey=api_key)
    res=service.cse().list(
        q=query,
        num=1,
        safe='off',
        searchType="image",
        cx='005353110374443367689:pdf513qmws8',
    ).execute()
    result = res.get('items')[0].get('link')
    return result

def define(input):
    """
    Searches the Merriam-Webster Learner's Dictionary for an input.\n
    Requires an API key and gives one definition per type of word.
    """
    dictionary = LearnersDictionary('')
    try:
        defs = [(entry.word, entry.function, definition)
                for entry in dictionary.lookup(input)
                for definition, examples in entry.senses]
    except WordNotFoundException:
        return "I couldnt find a definition for " + input + "."

    cats = []
    result = []
    for word, pos, definition in defs:
        if pos not in cats and word == input:
            result.append("*{0}*. {1}".format(pos, definition))
            cats.append(pos)
    return "**{0}**: {1}".format(input, ". ".join(result))

def search(query):
    return duckduckgo.get_zci(query)

def searchparse(input_txt):
    cmd = input_txt[6:10]
    try:
        if cmd == 'text':
            result = search(input_txt[11:])
            return result
        elif cmd == 'defn':
            result = define(input_txt[11:])
            return result
        elif cmd == 'imge':
            result = image(input_txt[11:])
            return result
        else:
            return "Something went wrong and it's probably your fault."
    except:
        return "Something went wrong and it's probably your fault."
