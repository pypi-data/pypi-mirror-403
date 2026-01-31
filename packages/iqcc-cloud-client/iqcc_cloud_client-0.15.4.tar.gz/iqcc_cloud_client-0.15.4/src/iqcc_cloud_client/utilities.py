from pathlib import Path
import base64
import os
import json

# from qiskit.transpiler import InstructionProperties, Target
from qiskit.transpiler import Target

# from qiskit.circuit import IfElseOp, WhileLoopOp, library
from qiskit.providers.backend import BackendV2
from qiskit.providers import Options
from qiskit.qasm3 import dumps as qasm3_dumps


def format_json_dense_arrays(
    obj,
    indent=2,
    level=0,
    max_items=20,
    show_truncation=True,
):
    pad = " " * (indent * level)
    next_pad = " " * (indent * (level + 1))

    if isinstance(obj, dict):
        items = []
        for k, v in obj.items():
            value = format_json_dense_arrays(
                v, indent, level + 1, max_items, show_truncation
            )
            items.append(f"\n{next_pad}{json.dumps(k)}: {value}")
        return "{" + ",".join(items) + f"\n{pad}" + "}"

    if isinstance(obj, list):
        truncated = obj[:max_items]
        parts = [
            json.dumps(x)
            if not isinstance(x, (dict, list))
            else format_json_dense_arrays(
                x, indent, level, max_items, show_truncation
            )
            for x in truncated
        ]

        if show_truncation and len(obj) > max_items:
            parts.append(json.dumps(f"... {len(obj) - max_items} more items"))

        return "[" + ", ".join(parts) + "]"

    return json.dumps(obj)


class _QiskitBackendQM(BackendV2):
    def __init__(self, target: Target, run):
        super().__init__(
            provider=None,
            name=f"QiskitBackendQM_{target.num_qubits}q",
            description=f"This is a device with {target.num_qubits} qubits.",
            backend_version="",
        )
        self._run = run
        self._target = target

    def run(self, circuit, **options):
        return self._run(
            qasm3_dumps(circuit), **options
        )  ## STILL NOT QISKIT JOB!

    def _default_options(self):
        return Options(num_shots=100, terminal_output=False, debug=False)

    @property
    def target(self):
        return self._target

    @property
    def max_circuits(self):
        return None


def _create_payload(folder_path, max_total_mb=8, max_file_mb=8):
    payload = {}
    total_bytes = 0
    max_total_bytes = max_total_mb * 1024 * 1024
    max_file_bytes = max_file_mb * 1024 * 1024

    if type(folder_path) is not str:
        # this is already expanded payload
        return folder_path

    # List all files in the folder (non-recursive)

    directory = Path(folder_path)
    files = [f for f in directory.rglob("*") if f.is_file()]

    for file_name in files:
        file_path = file_name

        file_size = os.path.getsize(file_path)

        if file_size > max_file_bytes:
            print(
                f"NOTE: Skipping {file_name} since it's size {file_size} is over maximal allowed one {max_file_bytes}."
            )
            continue

        if total_bytes + file_size > max_total_bytes:
            raise ValueError(
                f"Total size of upload directory cannot exceed {max_total_bytes}. Current size {total_bytes + file_size}"
            )

        # Read and base64 encode file
        with open(file_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")

        relative_path = file_path.relative_to(directory)
        payload[Path(relative_path).as_posix()] = encoded
        total_bytes += file_size
    return payload


def _complex_decoder(obj):
    if "__type__" in obj and obj["__type__"] == "complex":
        return complex(obj["data"][0], obj["data"][1])
    return obj


def _truncate_strings(obj, max_length=300):
    if isinstance(obj, str):
        return obj[:max_length] + ("..." if len(obj) > max_length else "")
    elif isinstance(obj, list):
        return [_truncate_strings(item, max_length) for item in obj]
    elif isinstance(obj, dict):
        return {
            key: _truncate_strings(value, max_length)
            for key, value in obj.items()
        }
    return obj


def _resolve_files(options: dict):
    hooks = ["pre_hook", "sync_hook", "post_hook"]
    for h in hooks:
        if h in options.keys():
            if type(options[h]) is str:
                with open(options[h], "r") as f:
                    options[h] = f.read()
            elif type(options[h]) is dict:
                for key in options[h].keys():
                    if key not in [
                        "user-cache-ref",
                        "image",
                        "directory",
                        "execute",
                    ]:
                        raise ValueError(
                            f"{h} should be either a string to filename or dict with 'user-cache-ref' key"
                        )
                    if key == "directory":
                        options[h]["directory"] = _create_payload(
                            options[h]["directory"]
                        )
