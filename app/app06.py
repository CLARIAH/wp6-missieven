import types
from tf.advanced.app import App


MODIFIERS = "remark folio ref emph und super special".strip().split()


def fmt_layoutFull(app, n, **kwargs):
    return app._wrapHtml(n, "trans", "punc", "")


def fmt_layoutFullNotes(app, n, **kwargs):
    return app._wrapHtml(n, "trans", "punc", "", notes=True)


def fmt_layoutRemark(app, n, **kwargs):
    return app._wrapHtml(n, "trans", "punc", "r")


def fmt_layoutRemarkNotes(app, n, **kwargs):
    return app._wrapHtml(n, "trans", "punc", "r", notes=True)


def fmt_layoutOrig(app, n, **kwargs):
    return app._wrapHtml(n, "trans", "punc", "o")


def fmt_layoutOrigNotes(app, n, **kwargs):
    return app._wrapHtml(n, "trans", "punc", "o", notes=True)


class TfApp(App):
    def __init__(app, *args, **kwargs):
        app.fmt_layoutFull = types.MethodType(fmt_layoutFull, app)
        app.fmt_layoutFullNotes = types.MethodType(fmt_layoutFullNotes, app)
        app.fmt_layoutRemark = types.MethodType(fmt_layoutRemark, app)
        app.fmt_layoutRemarkNotes = types.MethodType(fmt_layoutRemarkNotes, app)
        app.fmt_layoutOrig = types.MethodType(fmt_layoutOrig, app)
        app.fmt_layoutOrigNotes = types.MethodType(fmt_layoutOrigNotes, app)
        super().__init__(*args, **kwargs)

    def _wrapHtml(app, n, ft, after, kind, notes=False):
        api = app.api
        F = api.F
        Fs = api.Fs
        after = Fs(f"{after}{kind}").v(n) or ""
        material = Fs(f"{ft}{kind}").v(n) or ""
        clses = " ".join(cf for cf in MODIFIERS if Fs(cf) and Fs(cf).v(n))
        noteMaterial = F.fnote.v(n)
        if notes:
            noteMaterial = (
                f'<span class="fbody">«{noteMaterial}»</span>' if noteMaterial else ""
            )
        else:
            noteMaterial = '<span class="fmark">*</span>' if noteMaterial else ""
        if clses:
            material = f'<span class="{clses}">{material}</span>'
        return f"{material}{noteMaterial}{after}"
