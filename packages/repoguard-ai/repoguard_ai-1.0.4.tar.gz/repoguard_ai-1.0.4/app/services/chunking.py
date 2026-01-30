import re
from app.models.chunk import Chunk

def chunker(text:str,authority:str)->list[Chunk]:
    check_heading=re.compile(r"""
        ^\s*(\#{1,6}\s+[^\n]+)$
        |
        ^\s*<h([1-6])[^>]*>(.*?)</h\2>
        """,
        re.MULTILINE | re.IGNORECASE | re.VERBOSE 

        )
    chunks=[]
    current_heading="INTRO"
    last_end=0
    matches=check_heading.finditer(text)
    for match in matches:
        start = match.start()

        # save content before this heading
        content = text[last_end:start].strip()
        if content:
            chunks.append(
                Chunk(
                    authority=authority,
                    heading= current_heading,
                    content=content
                )
            )

        # extract heading text
        if match.group(1):  # markdown
            current_heading = match.group(1).lstrip("#").strip()
        else:  # html
            current_heading = re.sub(r"<[^>]+>", "", match.group(3)).strip()

        last_end = match.end()

    # trailing content
    tail = text[last_end:].strip()
    if tail:
        chunks.append(
            Chunk(
                authority=authority,
                heading= current_heading,
                content=tail
                ))
    return chunks

if __name__ == "__main__":
    sample = """
    <p align="center">
  <img src="logo.png" />
</p>
 <h1> rock </h1>
<p>Build fast and reliable apps</p>

# Installation
    """

    chunks = chunker(sample)
    for c in chunks:
        print("----")
        print(c["heading"])
        print(c["content"])
    
