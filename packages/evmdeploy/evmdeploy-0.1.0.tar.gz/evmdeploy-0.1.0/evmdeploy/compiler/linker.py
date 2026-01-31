def link_bytecode(bytecode: str, link_refs: dict, libraries: dict) -> str:
    """
    Replace library placeholders in bytecode.
    Args:
        bytecode: raw bytecode
        link_refs: from solc output
        libraries: {library_name: address}
    """
    bytecode_bytes = bytearray.fromhex(bytecode)

    for file, libs in link_refs.items():
        for lib_name, refs in libs.items():
            if lib_name not in libraries:
                raise ValueError(f"Missing library address for {lib_name}")

            address = libraries[lib_name].replace("0x", "")
            if len(address) != 40:
                raise ValueError(f"Invalid library address for {lib_name}")

            for ref in refs:
                start = ref["start"] * 2
                length = ref["length"] * 2
                bytecode_bytes[start : start + length] = bytes.fromhex(address)

    return "0x" + bytecode_bytes.hex()
