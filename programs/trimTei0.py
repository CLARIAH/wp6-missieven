def trimPage(text, *args):
    text = text.replace(''' rend=""''', "")
    text = text.replace(''' rend=" "''', "")
    return text
