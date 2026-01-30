    import subprocess
    process = subprocess.Popen(["less"], stdin=subprocess.PIPE)

    try:
        #process.stdin.write(b"test")
        original_write = process.stdin.write
        def print_wrapper(stuff):
            if process.stdin.closed:
                return
            if isinstance(stuff, str):
                original_write(bytes(stuff, encoding="utf-8"))
            else:
                original_write(stuff)
        output_to = process.stdin
        process.stdin.write = print_wrapper
        process.communicate()
    except IOError as e:
        pass
