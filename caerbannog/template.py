import os
import traceback
from caerbannog import context, target
from caerbannog.error import CaerbannogError

from jinja2 import Environment, FileSystemLoader, StrictUndefined, UndefinedError


def _join_paths(paths, separator):
    joined = os.path.join(*paths)

    if separator is not None:
        return joined.replace(os.sep, separator)

    return joined


def _create_environment() -> Environment:
    env = Environment()
    env.filters["join_path"] = _join_paths
    env.globals["is_targeted"] = target.is_targeted

    env.undefined = StrictUndefined

    # For more details, see
    # https://jinja.palletsprojects.com/en/3.1.x/templates/#whitespace-control
    env.trim_blocks = True
    env.lstrip_blocks = True
    env.keep_trailing_newline = True

    for k, v in context.settings().jinja_globals().items():
        env.globals[k] = v

    env.loader = FileSystemLoader(context.current_role_dir())
    return env


def render(*path: str):
    env = _create_environment()

    joined = _join_paths(path, None)

    template = env.get_template(joined)
    try:
        return template.render(context.context())
    except UndefinedError as e:
        # This is a little dubious, but if it ever fails, we'll find out soon enough.
        TEMPLATE_FRAME_OFFSET = 3
        frame = traceback.extract_tb(e.__traceback__)[TEMPLATE_FRAME_OFFSET]
        raise CaerbannogError.from_frame(f"Error rendering '{joined}': {e.message}", frame)
