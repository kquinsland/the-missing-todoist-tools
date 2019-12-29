from os import walk


def do():
    """
    Walk a directory, splitting all folder/file.md patterns into
    action names: folder_file and the relative file path for markdown
    :return:
    """
    # Get the current working directory
    _cwd = '.'
    # The name of each directory will be the component
    print("Walking _cwd:{}".format(_cwd))
    _dirs = walk(_cwd)

    # Full map
    _actions = {}

    for _d in _dirs:
        # _d will be a truple, first item is name, third is list of files inside the dir
        # Each file inside the dir represents an action that can be taken on that component.
        # E.G.: label/apply.md = action called: label_apply
        ##
        _cmp = _d[0].replace('./', '')
        _files = _d[2]

        if _cmp == '.':
            continue

        _actions[_cmp] = {}

        for _f in _files:
            # Ignore OSX crap and non MD files
            if not _f.endswith('.md'):
                continue
            # Otherwise, drop the .md extension
            _action = _f.replace('.md', '')

            # Then take the action, combine with component to get the full thing
            _action_name = "{}_{}".format(_cmp, _action)

            _actions[_cmp][_action_name] = "{}/{}".format(_cmp, _f )

    print("Write out actions from {} components...".format(len(_actions)))
    _render(_actions)


def _render(actions: dict):
    """
    Generates markdown that looks something like this

        # All Supported Actions

        ## `label_*`

        - [`label_create`](label/create.md)

        <etc>


    :param actions:
    :return:
    """
    # String to write to disk
    _document = ""

    # Some stats :)
    _components = 0
    _actions_total = 0

    for _cmp in actions:
        _components += 1
        # Create a new heading
        _document += "## `{}_*`\nThere are {} documented actions:\n".format(_cmp, len(actions[_cmp]))

        for _action, _file in actions[_cmp].items():
            _document += "- [`{}`]({})\n".format(_action, _file)
            _actions_total += 1
        _document += "\n"

    _document += "\nIn total, {} actions across {} components\n".format(_actions_total, _components)

    with open('readme.md', 'w+') as f:
        f.write(_document)
        f.close()


if __name__ == "__main__":
    print("doing!")
    do()
    print("Out!")
    exit()