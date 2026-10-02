from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from app.core.config import PROJECT_ROOT

environment = Environment(
    loader=FileSystemLoader(PROJECT_ROOT / "app" / "templates"),
    autoescape=select_autoescape(
        enabled_extensions=("html", "htm", "xml"), default_for_string=True, default=True
    ),
    undefined=StrictUndefined,
)
templates = Jinja2Templates(env=environment)
