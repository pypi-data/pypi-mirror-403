# corallium

CLI utility functions extracted from Calcipy.

## Installation

1. `poetry add corallium`

1. Take advantage of the logger or other common functionality

    ```sh
    form corallium.log import LOGGER

    LOGGER.info('Hello!')
    ```

## Usage

- **log**: Configure and use the global logger

    ```python
    from corallium.log import LOGGER, configure_logger
    import logging

    configure_logger(log_level=logging.INFO)
    LOGGER.info('Processing started', item_count=42)
    ```

- **pretty_process**: Run parallel tasks with progress bars

    ```python
    from corallium.pretty_process import pretty_process


    def task(task_id, shared_progress, data):
        for item in data:
            process(item)
            shared_progress[task_id] += 1
        return len(data)


    results = pretty_process(task, data=items, num_workers=4)
    ```

- **shell**: Execute shell commands with output capture

    ```python
    from corallium.shell import capture_shell

    output = capture_shell('git status', timeout=30)
    ```

- **file_helpers**: File utilities and project configuration

    ```python
    from corallium.file_helpers import find_in_parents, read_pyproject

    pyproject = read_pyproject()
    lock_path = find_in_parents(name='uv.lock')
    ```

- **tomllib**: Backport wrapper for TOML parsing (Python \<3.11 compatibility)

    ```python
    from corallium.tomllib import tomllib

    data = tomllib.loads(content)
    ```

- **dot_dict**: Wrapper for dotted-dictionary access via [Python-Box](https://pypi.org/project/python-box/)

    ```python
    from corallium.dot_dict import ddict

    config = ddict({'nested': {'value': 42}})
    print(config.nested.value)
    ```

For more example code, see the [scripts] directory or the [tests].

## Project Status

See the `Open Issues` and/or the [CODE_TAG_SUMMARY]. For release history, see the [CHANGELOG].

## Contributing

We welcome pull requests! For your pull request to be accepted smoothly, we suggest that you first open a GitHub issue to discuss your idea. For resources on getting started with the code base, see the below documentation:

- [DEVELOPER_GUIDE]
- [STYLE_GUIDE]

## Code of Conduct

We follow the [Contributor Covenant Code of Conduct][contributor-covenant].

### Open Source Status

We try to reasonably meet most aspects of the "OpenSSF scorecard" from [Open Source Insights](https://deps.dev/pypi/corallium)

## Responsible Disclosure

If you have any security issue to report, please contact the project maintainers privately. You can reach us at [dev.act.kyle@gmail.com](mailto:dev.act.kyle@gmail.com).

## License

[LICENSE]

[changelog]: https://corallium.kyleking.me/docs/CHANGELOG
[code_tag_summary]: https://corallium.kyleking.me/docs/CODE_TAG_SUMMARY
[contributor-covenant]: https://www.contributor-covenant.org
[developer_guide]: https://corallium.kyleking.me/docs/DEVELOPER_GUIDE
[license]: https://github.com/kyleking/corallium/blob/main/LICENSE
[scripts]: https://github.com/kyleking/corallium/blob/main/scripts
[style_guide]: https://corallium.kyleking.me/docs/STYLE_GUIDE
[tests]: https://github.com/kyleking/corallium/blob/main/tests
