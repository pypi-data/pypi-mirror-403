from collections.abc import Generator
import json


def json_pretty_store(gen: Generator, filename: str) -> None:
    """
    Format objects produced by generator then send to JSON file
    """
    with open(filename, 'w') as f:
        for matrix, a, b in gen:
            pretty = []
            for i in matrix:
                row = [str(x) for x in i]
                pretty += ["".join(row)]
            payload = {
                "A": a,
                "B": b,
                "Product": int(a, 2) * int(b, 2),
                'Stage_0': {
                    'Matrix': pretty,
                    },
            }
            json.dump(payload, f, indent=4)
