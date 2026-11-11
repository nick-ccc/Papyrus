from datetime import datetime
from langchain_core.tools import tool


@tool
def get_current_date() -> str:
  """Returns the current date in YYYY-MM-DD format."""
  return datetime.now().strftime("%Y-%m-%d")
