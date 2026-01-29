
def htmlpraser(content):
    n = 0 
    parsed_content = ""
    passed = False
    for i in content:
        if i == "<" or (i == "&" and content[n+1] == "#"):
            passed = True
        elif i == ">"  or i == ";":
            passed = False

        if not passed and not (i == "<" or i == ">" or i == ";"):
            parsed_content += i
        n += 1

    return parsed_content

