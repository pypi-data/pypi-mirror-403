from app.utils.load import load_chunks
from app.db import get_conn
from app.prompt_builder import build_prompt
from app.utils.search import sim_search
from app.services.generation import call_gemini
from app.models.validation import Validation

def run_validate(repo_id:str,diff:str,connect):
    #get the diff/code change

    #load the saved chunks of readme/coc/guidelines from db
    chunks=load_chunks(connect,repo_id)

    #get the top k chunks to reason on
    relevant_chunk=sim_search(diff,chunks)

    #build the prompt
    prompt=build_prompt(relevant_chunk,diff=diff)

    #call the ai api key
    generation=call_gemini(prompt=prompt)
    #print("RAW MODEL OUTPUT:\n", generation)

    try:
      raw = generation.strip()

      # Remove markdown code fences
      if raw.startswith("```"):
        raw = raw.split("```")[1].strip()

      # Trim to JSON object
      start = raw.find("{")
      end = raw.rfind("}") + 1
      raw = raw[start:end]
      result = Validation.model_validate_json(raw)
      return result
    except Exception as e:
      print("PARSING ERROR:", e)
      return Validation(
        status="Warning",
        explanation="Validator could not produce a structured response.",
        violated_guidelines=[]
      )