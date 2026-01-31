import sys, os
import json

if not "DEBUG" in os.environ:
    if sys.stdin.isatty():
        print("No input provided. Please pipe data into this script.", file=sys.stderr)
        sys.exit(1)
    input = sys.stdin
else:
    from tqdm import tqdm
    folder = "/home/jonas/rl-tools/src/foundation_policy/dynamics_parameters"
    input = []
    for file in tqdm(os.listdir(folder)):
        if file.endswith(".json"):
            with open(os.path.join(folder, file), 'r') as f:
                input.append(f.read())
    input = input[:10]

data = []
header = []

def get_value_from_dict(path, obj):
    path_parts = path.split('.')
    if len(path_parts) == 1:
        return obj[path_parts[0]] if path_parts[0] in obj else None
    else:
        return get_value_from_dict('.'.join(path_parts[1:]), obj[path_parts[0]]) if path_parts[0] in obj else None
def flatten(obj):
    if not isinstance(obj, dict) and not isinstance(obj, list):
        raise ValueError("Input must be a dictionary or a list")
    if isinstance(obj, dict):
        items = obj.items()
    elif isinstance(obj, list):
        items = enumerate(obj)
    for key, value in items:
        if isinstance(value, dict) or isinstance(value, list):
            for inner_key, inner_value in flatten(value):
                yield ".".join([str(key), str(inner_key)]), inner_value
        else:
            yield str(key), value


def main():
    keys = set()
    data = []
    for line in input:
        json_data = line.strip()
        json_obj = json.loads(json_data)
        items = dict(flatten(json_obj))
        data.append(items)
        keys.update(items.keys())


    keys = sorted(keys)

    print(",".join(keys))
    for row in data:
        output_row = []
        for key in keys:
            value = row.get(key, None)
            if isinstance(value, str):
                value = value.replace(",", " ")
            elif value is None:
                value = ""
            output_row.append(str(value))
        print(",".join(output_row))



if __name__ == "__main__":
    main()