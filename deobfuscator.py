import re


def decode_lua_escapes(text: str) -> str:
    replacements = {
        r"\n": "\n",
        r"\t": "\t",
        r"\r": "\r",
        r"\"": '"',
        r"\'": "'",
        r"\\": "\\",
    }

    for escaped, real in replacements.items():
        text = text.replace(escaped, real)

    text = re.sub(
        r"\\(\d{1,3})",
        lambda match: chr(int(match.group(1)) & 0xFF),
        text
    )

    text = re.sub(
        r"\\x([0-9A-Fa-f]{2})",
        lambda match: chr(int(match.group(1), 16)),
        text
    )

    return text


def clean_source(source: str) -> str:
    source = re.sub(r"(?m)^\s*--.*$", "", source)
    source = re.sub(r"\n{3,}", "\n\n", source)

    cleaned_lines = []

    for line in source.splitlines():
        line = line.rstrip()

        if line:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def convert_hex_numbers(source: str) -> str:
    return re.sub(
        r"\b0x([0-9A-Fa-f]+)\b",
        lambda match: str(int(match.group(1), 16)),
        source
    )


def extract_string_tables(source: str):
    tables = []

    table_pattern = re.compile(
        r"(?:local\s+)?([A-Za-z_]\w*)\s*=\s*\{([^{}]*)\}",
        re.DOTALL
    )

    string_pattern = re.compile(r'"((?:\\.|[^"\\])*)"')

    for match in table_pattern.finditer(source):
        name = match.group(1)
        body = match.group(2)

        strings = string_pattern.findall(body)

        if len(strings) >= 3:
            decoded_strings = [
                decode_lua_escapes(value)
                for value in strings
            ]

            tables.append((name, decoded_strings))

    return tables


def deobfuscate_lua(source: str):
    report = []
    original = source

    source = clean_source(source)

    if source != original:
        report.append("Removed comments and normalized formatting.")

    original = source
    source = convert_hex_numbers(source)

    if source != original:
        report.append("Converted hexadecimal numbers to decimal.")

    tables = extract_string_tables(source)

    if tables:
        report.append(
            f"Recovered {len(tables)} possible string table(s)."
        )

        table_report = ["-- Recovered string tables --"]

        for name, values in tables:
            table_report.append(f"{name}:")

            for index, value in enumerate(values):
                table_report.append(f"  [{index}] {value!r}")

        report.append("\n".join(table_report))

    return source, "\n".join(report)
