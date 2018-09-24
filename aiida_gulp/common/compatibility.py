def aiida_version():
    """get the version of aiida in use

    :returns: packaging.version.Version
    """
    from aiida import __version__ as aiida_version_
    from packaging import version
    return version.parse(aiida_version_)


def cmp_version(string):
    """convert a version string to a packaging.version.Version"""
    from packaging import version
    return version.parse(string)


def run_get_node(process, inputs_dict):
    """ an implementation of run_get_node which is compatible with both aiida v0.12 and v1.0.0

    it will also convert "options" "label" and "description" to/from the _ variant

    :param process: a process
    :param inputs_dict: a dictionary of inputs
    :type inputs_dict: dict
    :return: the calculation Node
    """
    if aiida_version() < cmp_version("1.0.0a1"):
        for key in ["options", "label", "description"]:
            if key in inputs_dict:
                inputs_dict["_" + key] = inputs_dict.pop(key)
        workchain = process.new_instance(inputs=inputs_dict)
        workchain.run_until_complete()
        calcnode = workchain.calc
    else:
        from aiida.work.launch import run_get_node  # pylint: disable=import-error
        for key in ["_options", "_label", "_description"]:
            if key in inputs_dict:
                inputs_dict[key[1:]] = inputs_dict.pop(key)
        _, calcnode = run_get_node(process, **inputs_dict)

    return calcnode