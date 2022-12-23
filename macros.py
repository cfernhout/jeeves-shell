"""MkDocs macros for the documentation site."""
import functools
import operator
import tempfile
from pathlib import Path
from typing import List, Optional, Dict

from mkdocs_macros.plugin import MacrosPlugin
from plumbum.cmd import python, j as jeeves, bash


PYTHON_TEMPLATE = '''
```python title="{path}"
{code}
```

{annotations}

⇒
```python title="{cmd} {path}"
{stderr}
{stdout}
```
'''


JEEVES_TEMPLATE = '''
``` title="↦ <code>{cmd}</code>"
{stdout}
```
'''


TERMINAL_TEMPLATE = '''
``` title="↦ <code>{title}</code>"
{output}
```
'''

CODE_TEMPLATE = '''
```{language} title="{title}"
{code}
```
'''


def format_annotations(annotations: List[str]) -> str:
    enumerated_annotations = enumerate(annotations, start=1)

    return '\n\n'.join(
        f'{number}. {annotation}'
        for number, annotation in enumerated_annotations
    )



def code(
    path: str,
    docs_dir: Path,
    language: Optional[str] = None,
    title: Optional[str] = None,
):
    content = (docs_dir / path).read_text()

    return CODE_TEMPLATE.format(
        language=language,
        code=content,
        title=title or path,
    )


def run_python_script(
    path: str,
    docs_dir: Path,
    annotations: Optional[List[str]] = None,
    args: Optional[List[str]] = None,
):
    if annotations is None:
        annotations = []

    if args is None:
        args = []

    code_path = docs_dir / path
    code = code_path.read_text()

    _, stdout, stderr = python.run(*args, code_path, retcode=None)

    cmd = 'python'
    if args:
        formatted_args = ' '.join(args)
        cmd = f'{cmd} {formatted_args}'

    return PYTHON_TEMPLATE.format(
        path=path,
        code=code,
        stdout=stdout,
        stderr=stderr,
        annotations=format_annotations(annotations),
        cmd=cmd,
    )


def j(
    path: str,
    docs_dir: Path,
    annotations: Optional[List[str]] = None,
    args: Optional[List[str]] = None,
    environment: Optional[Dict[str, str]] = None,
):
    if annotations is None:
        annotations = []

    if args is None:
        args = []

    code_path = docs_dir / path
    code = code_path.read_text()

    with tempfile.TemporaryDirectory() as raw_directory:
        directory = Path(raw_directory)

        (directory / 'jeeves.py').write_text(code)

        _, stdout, stderr = operator.getitem(jeeves, args).with_cwd(
            directory,
        ).with_env(
            **(environment or {}),
        ).run(retcode=None)

    cmd = 'j'
    if args:
        formatted_args = ' '.join(args)
        cmd = f'{cmd} {formatted_args}'

    return JEEVES_TEMPLATE.format(
        path=path,
        code=code,
        stdout=stdout,
        stderr=stderr,
        annotations=format_annotations(annotations),
        cmd=cmd,
    )


def terminal(
    command: str,
    title: Optional[str] = None,
    environment: Optional[Dict[str, str]] = None,
    cwd: Optional[str] = None,
):
    execute = bash['-c'].with_env(
        **(environment or {}),
    )

    if cwd:
        execute = execute.with_cwd(cwd)

    output = execute(command)

    return TERMINAL_TEMPLATE.format(
        output=output,
        title=title or command,
    )

def define_env(env: MacrosPlugin):
    """Hook function."""
    env.macro(
        functools.partial(
            run_python_script,
            docs_dir=Path(env.conf['docs_dir']),
        ),
        name='run_python_script',
    )

    env.macro(
        functools.partial(
            j,
            docs_dir=Path(env.conf['docs_dir']),
        ),
        name='j',
    )

    env.macro(
        functools.partial(
            code,
            docs_dir=Path(env.conf['docs_dir']),
        ),
        name='code',
    )

    env.macro(terminal)