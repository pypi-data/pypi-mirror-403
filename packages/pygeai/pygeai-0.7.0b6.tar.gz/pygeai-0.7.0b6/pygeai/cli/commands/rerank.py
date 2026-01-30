import json
from pygeai.cli.commands import Command, Option, ArgumentsEnum
from pygeai.cli.commands.builders import build_help_text
from pygeai.cli.texts.help import RERANK_HELP_TEXT
from pygeai.core.common.exceptions import MissingRequirementException, WrongArgumentError
from pygeai.core.rerank.clients import RerankClient
from pygeai.core.utils.console import Console


def show_help():
    """
    Displays help text in stdout
    """
    help_text = build_help_text(rerank_commands, RERANK_HELP_TEXT)
    Console.write_stdout(help_text)


def rerank_chunks(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    query = opts.get('query')
    model = opts.get('model')
    top_n = opts.get('top_n', 3)
    documents_arg = opts.get('documents')
    
    documents = []
    if documents_arg:
        if "[" not in documents_arg:
            documents.append(documents_arg)
        else:
            try:
                documents_json = json.loads(documents_arg)
                if not isinstance(documents_json, list):
                    raise ValueError

                documents = documents_json
            except Exception:
                raise WrongArgumentError(
                    "Documents must be a list of strings: '[\\\"text_chunk_1\\\", \\\"text_chunk_2\\\"]'. "
                    "Each element in the list must be a string representing a text chunk.."
                )

    if not (model and query and documents):
        raise MissingRequirementException("Cannot rerank chunks without model, query and documents")

    client = RerankClient()
    result = client.rerank_chunks(
        query=query,
        model=model,
        documents=documents,
        top_n=top_n
    )
    Console.write_stdout(f"Rerank details: \\n{result}")


rerank_chunks_options = [
    Option(
        "query",
        ["--query", "-q"],
        "string: Input query",
        True
    ),
    Option(
        "model",
        ["--model", "-m"],
        "string: provider/modelName reranker to use; supported values: cohere/rerank-v3.5, "
        "awsbedrock/cohere.rerank-v3.5, awsbedrock/amazon.rerank-v1",
        True
    ),
    Option(
        "documents",
        ["--documents", "--doc", "-d"],
        "string or array: A list of text chunks",
        True
    ),
    Option(
        "top_n",
        ["--top-n"],
        "string: Count of best n results to return",
        True
    ),

]


rerank_commands = [
    Command(
        "help",
        ["help", "h"],
        "Display help text",
        show_help,
        ArgumentsEnum.NOT_AVAILABLE,
        [],
        []
    ),
    Command(
        "rerank",
        ["rerank-chunks", "chunks", "rc"],
        "Rerank chunks based on a query",
        rerank_chunks,
        ArgumentsEnum.REQUIRED,
        [],
        rerank_chunks_options
    ),
]
