# Evaluate - log a run
import promptquality as pq
from promptquality import EvaluateRun, Scorers
from openai import OpenAI
import pandas as pd
from promptquality import Scorers
from promptquality import SupportedModels
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

GALILEO_PROJECT_NAME = 'washpost_rag_upload'
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

pq.login("https://console.dev.rungalileo.io/")

metrics = [
    Scorers.correctness
]

data = pd.read_csv('news_qa_dataset.csv')

df = pd.DataFrame(data)

dataset = {
    "input": df['query'].tolist(),
    "documents": [
        [pq.Document(content=content, metadata={"length": len(content)})] for content in df['context'].tolist()
    ],
    "output": df['answer'].tolist(),
    "ground_truth": df['answer'].tolist()
}

evaluate_run = EvaluateRun(
    scorers=[Scorers.correctness],
    project_name=GALILEO_PROJECT_NAME
)

template = """
    Use the following pieces of context to answer the question.
    ```
    {context}
    ```
    Question: {question}
"""

for i in range(len(dataset["input"])):

    wf = evaluate_run.add_workflow(input=dataset["input"][i], output=dataset["output"][i], duration_ns=2000, ground_truth=dataset["ground_truth"][i])

    wf.add_retriever(
        input=dataset["input"][i],
        documents=dataset["documents"][i],
        duration_ns=1000
    )
    
    prompt = template.format(context="\n\n".join([document.content for document in dataset["documents"][i]]), question=dataset["input"][i])

    wf.add_llm(
        input=pq.Message(content=prompt, role=pq.MessageRole.user),
        output=pq.Message(content=dataset["output"][i], role=pq.MessageRole.assistant),
        model=pq.Models.chat_gpt,
        input_tokens=25,
        output_tokens=6,
        total_tokens=31,
        duration_ns=1000
    )

evaluate_run.finish()
