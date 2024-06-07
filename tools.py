from openai import OpenAI

def model_list(client : OpenAI):
    models = client.models.list()
    for model in models:
        print(model.id)
