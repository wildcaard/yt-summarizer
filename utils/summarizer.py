import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

class APIError(Exception):
    """Raised when the API call or parsing fails."""
    pass

class SummaryStructure(BaseModel):
    short_summary: str = Field(description="A short summary in 2-3 sentences")
    key_takeaways: list[str] = Field(description="Exactly 5 key takeaways as strings")
    detailed_summary: str = Field(description="A detailed summary in a full paragraph")

def summarize(transcript_text: str) -> dict:
    """
    Summarizes the given transcript text.
    Returns a dictionary parsed from the LLM response with keys:
    'short_summary', 'key_takeaways', and 'detailed_summary'.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    model_name = os.getenv("OPENROUTER_MODEL", "openai/gpt-3.5-turbo")

    if not api_key:
        raise APIError("OPENROUTER_API_KEY is not set in the environment or .env file.")

    try:
        # Initialize ChatOpenAI pointing to OpenRouter
        llm = ChatOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
            model=model_name
        )

        # Set up parser using Pydantic model
        parser = JsonOutputParser(pydantic_object=SummaryStructure)

        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant that expertly summarizes video transcripts. You must return valid JSON matching the format instructions exactly."),
            ("user", "Analyze the following transcript and extract the requested summaries.\n\nFormatting Instructions:\n{format_instructions}\n\nTranscript:\n{transcript}")
        ])

        # Create the LangChain processing pipeline
        chain = prompt | llm | parser

        # Invoke the chain
        result = chain.invoke({
            "transcript": transcript_text,
            "format_instructions": parser.get_format_instructions(),
        })

        return result

    except Exception as e:
        raise APIError(f"OpenRouter API error: {str(e)}")
