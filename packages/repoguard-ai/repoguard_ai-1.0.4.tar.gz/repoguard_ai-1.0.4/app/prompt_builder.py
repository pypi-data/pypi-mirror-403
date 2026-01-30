from pathlib import Path

PROMPT_PATH=Path(__file__).parent/"prompts"/"validator.txt"

def build_prompt(chunks,diff:str):
    template=PROMPT_PATH.read_text()

    formatted_chunks_list = []

    for c in chunks:
      block = f"[{c.authority}] {c.heading}\n{c.content}"
      formatted_chunks_list.append(block)

    formatted_chunks = "\n\n".join(formatted_chunks_list)

    return template.format(
        guidelines=formatted_chunks,
        diff=diff
    )