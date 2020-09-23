processPage = None


def trimPage(text, *args, **kwargs):
    text = text.replace(''' rend=""''', "")
    text = text.replace(''' rend=" "''', "")
    return text
