import argparse
import asyncio
import logging
import os
import sys
import textwrap

from termcolor import colored, cprint

from filerohr.pipeline import File, Job, Pipeline, get_tasks, pipeline_progress


def _show_progress(name: str, progress: float | int):
    # A rather unintelligent progress bar implementation.
    name = f"\r{name}: "
    percentage = f" {round(progress):3}% "
    bar_size = os.get_terminal_size().columns
    bar_size -= len(name)
    bar_size -= len(percentage)
    full_block_count = round(bar_size * progress / 100)
    light_block_count = bar_size - full_block_count
    bar = f"{full_block_count * '█'}{light_block_count * '░'}"

    output = name + bar + percentage
    print(output, end="", file=sys.stderr, flush=True)


def _import_file(args):
    loop = asyncio.new_event_loop()
    config = Pipeline.get_config(args.config)
    pipeline = Pipeline.create(config)
    file = File.from_path(args.file_or_url, keep=True)
    if sys.stderr.isatty():

        def set_progress(pipeline: Pipeline, job: Job | None):
            if not job:
                return
            _show_progress(job.name, job.progress_percent or 0)

        pipeline_progress.connect(set_progress)
    processed_files = loop.run_until_complete(pipeline.start(file))
    for file in processed_files:
        print(file.model_dump_json(indent=2))
    if pipeline.status == "failed":
        sys.exit(1)
    if pipeline.status == "stopped":
        sys.exit(2)


def _show_version(args):
    from filerohr import __version__

    print(__version__)


def _serialize_type(info):
    value_type = info.get("type", None)
    if value_type == "array":
        subtype = _serialize_type(info["items"])
        if "|" in subtype:
            subtype = f"({subtype})"
        return f"{subtype}[]"
    const_value = info.get("const", None)
    if const_value:
        return repr(const_value)
    if value_type == "string" and (enum := info.get("enum", None)):
        return " | ".join(_repr(token) for token in enum)
    if value_type:
        return value_type
    any_of = info.get("anyOf", None)
    if any_of is not None:
        return " | ".join(_serialize_type(_info) for _info in any_of)
    return "unknown"


def _repr(value):
    if value is None:
        return "null"
    return repr(value)


def _list_jobs(args):
    sentinel = object()
    hpref = "#" * args.base_heading_level

    first = True
    for name, creator in sorted(get_tasks()):
        if not creator.advertise:
            continue
        if not first:
            print()
        else:
            first = False
        cprint(f"{hpref}# {name}", attrs=["bold"])
        if description := creator.job_description:
            cprint(description, attrs=["dark"])
        schema = creator.config.model_json_schema()
        properties = schema["properties"]
        del properties["job"]
        if not properties:
            print()
            continue

        cprint(f"{hpref}## Configuration options:\n", attrs=[])
        for property_key, info in properties.items():
            title = colored(property_key, attrs=[])
            if value_type := _serialize_type(info):
                title += f": `{value_type}`"
            if (default := info.get("default", sentinel)) is not sentinel:
                title += f", default: `{_repr(default)}`"
            else:
                title += ", " + colored("*required*", attrs=["underline"])
            cprint(f"{hpref}### {title}")

            if description := info.get("description", ""):
                text = textwrap.fill(description)
                print()
                cprint(text, attrs=["dark"])
            if examples := info.get("examples", []):
                print()
                print("Examples:")
                for example in examples:
                    text = f"`{_repr(example)}`"
                    text = textwrap.fill(text, initial_indent="- ", subsequent_indent="  ")
                    print(text)
            print()


def _validate_pipeline_config(args):
    config = Pipeline.get_config(args.config)
    print(config.model_dump_json(indent=2))
    config.check_best_practices()


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--log-level",
        default=logging.getLevelName(logging.WARNING),
        choices=logging.getLevelNamesMapping().keys(),
    )
    parser.add_argument("--version", action="store_const", const=_show_version)
    subparsers = parser.add_subparsers()
    process_file = subparsers.add_parser("import-file", help="Import file")
    process_file.add_argument("--config", help="Pipeline config file or name")
    process_file.add_argument("file_or_url", help="File or URL to process")
    process_file.set_defaults(func=_import_file)
    validate_pipeline_config = subparsers.add_parser(
        "validate-config", help="Loads and dumps the validated pipeline config."
    )
    validate_pipeline_config.add_argument("config", help="Pipeline config file or name")
    validate_pipeline_config.set_defaults(func=_validate_pipeline_config)
    list_jobs = subparsers.add_parser(
        "list-jobs",
        help="Show information on available jobs and their configuration options",
    )
    list_jobs.add_argument(
        "--base-heading-level",
        type=int,
        default=0,
        help="Markdown heading indent level",
    )
    list_jobs.set_defaults(func=_list_jobs)
    return parser


def main(args=None):
    parser = get_parser()
    parsed_args = parser.parse_args(args)

    logging.basicConfig(
        level=logging.getLevelNamesMapping()[parsed_args.log_level],
        handlers=[logging.StreamHandler()],
    )
    func = getattr(parsed_args, "func", None)
    if func is None:
        parser.print_help()
        sys.exit(1)
    else:
        func(parsed_args)


if __name__ == "__main__":
    main()
