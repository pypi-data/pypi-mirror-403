"""Utils for datapipe testing"""

import subprocess as sp


def run_cwl(workflow_path, inputs_path=None, cwd=None):
    """Run cwltool on a workflow using subprocess."""
    command = ["cwltool", "--debug", str(workflow_path)]
    if inputs_path is not None:
        command.append(str(inputs_path))
    return sp.run(command, stdout=sp.PIPE, stderr=sp.STDOUT, text=True, cwd=cwd)
