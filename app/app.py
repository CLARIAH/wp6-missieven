import types
from tf.advanced.app import App


MODIFIERS = "remark folio note ref emph und super special".strip().split()


def fmt_layoutFull(app, n, **kwargs):
    return app._wrapHtml(n, ("",))


def fmt_layoutRemarks(app, n, **kwargs):
    return app._wrapHtml(n, ("r",))


def fmt_layoutNotes(app, n, **kwargs):
    return app._wrapHtml(n, ("n",))


def fmt_layoutOrig(app, n, **kwargs):
    return app._wrapHtml(n, ("o",))


def fmt_layoutNoRemarks(app, n, **kwargs):
    return app._wrapHtml(n, ("o", "n"))


def fmt_layoutNoNotes(app, n, **kwargs):
    return app._wrapHtml(n, ("o", "r"))


def fmt_layoutNonOrig(app, n, **kwargs):
    return app._wrapHtml(n, ("r", "n"))


NOTE = "note"
WORD = "word"


class TfApp(App):
    def __init__(app, *args, **kwargs):
        app.fmt_layoutFull = types.MethodType(fmt_layoutFull, app)
        app.fmt_layoutRemarks = types.MethodType(fmt_layoutRemarks, app)
        app.fmt_layoutNotes = types.MethodType(fmt_layoutNotes, app)
        app.fmt_layoutOrig = types.MethodType(fmt_layoutOrig, app)
        app.fmt_layoutNoRemarks = types.MethodType(fmt_layoutNoRemarks, app)
        app.fmt_layoutNoNotes = types.MethodType(fmt_layoutNoNotes, app)
        app.fmt_layoutNonOrig = types.MethodType(fmt_layoutNonOrig, app)
        super().__init__(*args, **kwargs)

    def _wrapHtml(app, n, kinds):
        api = app.api
        F = api.F
        Fs = api.Fs
        L = api.L

        preNote = ""
        postNote = ""

        if "" in kinds or "n" in kinds:
            notes = L.u(n, otype=NOTE)
            if notes:
                note = notes[0]
                mark = F.mark.v(note)
                noteWords = L.d(note, otype=WORD)
                firstWord = noteWords[0]
                lastWord = noteWords[-1]
                if firstWord == n:
                    preNote = f"«{mark}= "
                if lastWord == n:
                    postNote = f" ={mark}»"

        material = "".join(Fs(f"trans{kind}").v(n) or "" for kind in kinds)
        after = "".join(Fs(f"punc{kind}").v(n) or "" for kind in kinds)
        material = f"{preNote}{material}{after}{postNote}"
        clses = " ".join(
            cf for cf in MODIFIERS if (fscf := Fs(f"is{cf}")) and fscf.v(n)
        )
        if clses:
            material = f'<span class="{clses}">{material}</span>'
        return material
