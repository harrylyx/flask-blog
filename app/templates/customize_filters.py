from app import app

@app.template_filter('get_summary')
def get_summary(text):
    idx = 800
    summary = text[:idx]
    if '<pre>' in summary and '</pre>' not in summary:
        idx = max(idx, text.index('</pre>') + len('</pre>'))
    if '<table>' in summary and '</table>' not in summary:
        idx = max(idx, text.index('</table>') + len('</table>'))
    summary = text[:idx] + " ..."
    return summary

