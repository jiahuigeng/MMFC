import time
import argparse
import os, json, re
import pandas as pd
from tqdm import tqdm
import sys
import requests
import os
url = "http://localhost:11434/api/generate"

headers = {
    'Content-Type': 'application/json'
}

LLAMA3_PROMPT = """You are a helpful AI assistant. Your are customized for a specific use case. 

You are required to summarize an article focusing on detailed fact-checking an image the following information: the type of image: (True: the image is authentic; Out-of-Context, the image is authentic but it is miscaptioned, misidentified, misrepresented, misappropriated) ; the topic; the background of the real image (the authentic image or image before manipulation; Manipulated: the image is digitally altered, morphed; AI-Generated: the image is ai-generated), when and where the image was taken and which event it is describing. 

You are required to specializes in creating structured JSON reports. The JSON report includes the following key entries: "type of image" (One of True, Out-of-Context, Manipulated, AI-Generated), "topic" (one of Politics, Entertainment, Business, Health&Science, Society, Environment and History) "real time", "real location" (better contains city and country within the string), "real event" (one sentence contains important details). When specific details are not available in the article, you need note "Not Enough Informaiton" for that entry. Responses are presented in a formal, technical style, ensuring accuracy and clarity.

Note: If the image is AI-generated, "real time", "real location", and "real event" will be "Not Enough Information".
"""

def llama3_prompting(content, model):
    payload = {
        "model": model,
        "prompt": content,
        "stream": False
    }
    resp = ""
    try:
        response_output_guard = requests.post(url, json=payload, headers=headers)

        if response_output_guard.status_code == 200:
            resp = response_output_guard.json()['response']
        else:
            print(f"Error: {response_output_guard.status_code}")

    except:
        print(f"Fail to post to LLama3")

    return resp

def label_corpus_llama3(corpus, model="llama3:8b", suffix=""):

    if corpus in ["fauxtography", "cosmos", "post4v"]:
        print(corpus)
        csvfile = os.path.join('dataset', corpus, f"{corpus}_data.csv")
        df_input = pd.read_csv(csvfile, encoding='ISO-8859-1')
        articles_folder = os.path.join('dataset', corpus, f"{corpus}_articles")

    annotated_path = "llama3_annotations_mmfc"
    if suffix:
        annotated_path = annotated_path + f"_{suffix}"
        if annotated_path not in os.listdir('dataset'):
            os.mkdir(f'dataset/{annotated_path}/')

        saved_jsonfile = os.path.join(f'dataset/{annotated_path}/', f"llama3_annotations_{corpus}.json")
        if os.path.isfile(saved_jsonfile):
            json_data = json.load(open(saved_jsonfile))
        else:
            json_data = dict()

        for index, row in df_input.iterrows():
            article_path = row["article_path"]
            claim = row["claim_en"]
            if claim in json_data:
                continue
            image_id = row["image_id"]
            print(index, row["claim_en"])
            if str(article_path) not in ["", "nan", "None"]:
                if article_path.startswith("dataset"):

                    content = LLAMA3_PROMPT + '\n\nArticle: \n' + open(article_path, encoding="utf-8").read()
                    llama3_output = llama3_prompting(content, model)
                    # print(llama3_output)
                    json_match = re.search(r'\{.*\}', llama3_output, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        json_str = re.sub("[‘’“”]", "\"", json_str)
                        try:
                            cur_data = json.loads(json_str)
                            print(cur_data)
                            cur_data["image_id"] = image_id
                            if row["claim_en"] not in json_data:
                                json_data[claim] = cur_data

                            json.dump(json_data, open(saved_jsonfile, 'w', encoding="utf-8"), indent=4)

                        except json.JSONDecodeError as e:
                            print(f"Error decoding JSON: {e}")
                            print(json_str)

                    else:
                        print(f"No match for {article_path}")
                        print(llama3_output)


            # if index > 10:
            #     break

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', type=str, default='llama3:70b')
    parser.add_argument('--corpus', type=str, default="post4v")
    parser.add_argument('--suffix', type=str, default="v1")
    args = parser.parse_args()
    if "llama3" in args.model:
        label_corpus_llama3(args.corpus, args.model, args.suffix)