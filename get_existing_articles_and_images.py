import pandas as pd
import os, json, string
import argparse
# from utils import contains_words
import requests
from bs4 import BeautifulSoup
from time import sleep


multimodal_ll = ["image", "pic", "photo", "video", "graph", "figure"]

def contains_words(text, ll, all=True):
    if all:
        return all([word in text for word in ll])
    else:
        return any([word in text for word in ll])

def get_context( type=None):


    if type == 'ooc':
        context = 'ooc'
    elif type == 'fake':
        context = "fake"
    else:
        context = ""
    pass


def remove_punctuation(text):
    # Create a translation table that maps each punctuation character to None
    translator = str.maketrans('', '', string.punctuation)

    return text.translate(translator)
def snopes_page_parse(url, more=False):
    claim, rating = None, None
    datePub, article = None, None

    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        script_tags = soup.find_all('script', {'type': 'application/ld+json'})

        for script in script_tags:
            data = json.loads(script.string)
            try:
                if data["@type"] == "ClaimReview":
                    claim = data["claimReviewed"]
                    rating = data["reviewRating"]["alternateName"].lower()
                    datePub = data["datePublished"]

            except:
                continue

        print(url)
        article = soup.find('article', {'id': 'article-content'}).get_text()
        if "About this rating" in article:
            article = article.split("About this rating")[1]


        article = "\n".join([para for para in article.split("\n") if para])
        print(article)

    return claim, rating, datePub, article




# url = "https://www.snopes.com/fact-check/1-million-dead-mosquitoes/"
# snopes_page_parse(url)
def collect_articles_and_images(data, image=False):
    csvfile = os.path.join("dataset", data, f'{data}_data.csv')
    # if args.data == "post4v":
    #     csvfile = os.path.join("dataset", args.data, "post4v_data.csv")
    #
    # elif args.data == "fauxtography":
    #     csvfile = os.path.join("dataset", args.data, "fauxtography_data.csv")
    #
    # elif args.data == "cosmos":
    #     csvfile = os.path.join("dataset", args.data, "cosmos_data.csv")
    cnt_mm = 0
    df_input = pd.read_csv(csvfile)


    if not "article_path" in df_input:
        df_input["article_path"] = None
    if not "datePub" in df_input:
        df_input["datePub"] = None
    if not "rating" in df_input:
        df_input["rating"] = None

    article_folder = os.path.join("dataset", data, "articles")
    if not os.path.exists(article_folder):
        os.makedirs(article_folder)

    for idx, row in df_input.iterrows():

        # if idx > 300:
        #     break
        claim = row["claim_en"]
        claim_url = row["claim_url"]

        if str(claim_url) in ["None", "nan", ""]:
            continue

        if str(row["datePub"]) in ["None", "nan", ""] or str(row["rating"]) in ["None", "nan", ""]:
            print(f"datePub idx {idx}")

            if not "snopes" in claim_url:
                continue

            _, rating, datePub, article = snopes_page_parse(claim_url)
            df_input.at[idx, "datePub"] = datePub
            df_input.at[idx, "rating"] = rating

            if not claim_url.startswith("http"):
                claim_url = f"https://{claim_url}"
                df_input.loc[idx, "claim_url"] = claim_url

            df_input.to_csv(csvfile, index=False)
            if data == "post4v":
                if not contains_words(claim.lower(), multimodal_ll, all=False) and not str(row["rating"]).lower() in ["fake", "miscaptioned"]:
                    continue
            else:
                if not contains_words(claim.lower(), multimodal_ll, all=False):
                    continue

            if str(row["article_path"]) in ["None", "nan", ""]:
                # print(claim)

                if '&quot;' in claim:
                    claim = claim.replace('&quot;', "'")
                    df_input.at[idx, "claim_en"] = claim

                article_name = claim_url.strip("/").split("/")[-1] + ".txt"
                article_path = os.path.join(article_folder, article_name)
                df_input.at[idx, "article_path"] = article_path
                with open(article_path, "w", encoding="utf-8") as f:
                    f.write(article)
                print(f"{article_path} idx {idx}")

                sleep(2)

                df_input.to_csv(csvfile, index=False)




if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, help="data name", default="post4v")

    args = parser.parse_args()
    collect_articles_and_images(args.data)
