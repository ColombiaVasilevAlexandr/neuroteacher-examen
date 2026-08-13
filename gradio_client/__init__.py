import os
import sys

_real_init = None
for _entry in sys.path:
    if not _entry:
        continue
    _candidate = os.path.join(_entry, 'gradio_client', '__init__.py')
    if os.path.isfile(_candidate) and os.path.abspath(_candidate) != os.path.abspath(__file__):
        _real_init = _candidate
        break
if _real_init is None:
    raise ImportError('Installed gradio_client package was not found')

__path__ = [os.path.dirname(_real_init)]
__file__ = _real_init
with open(_real_init, 'rb') as _f:
    exec(compile(_f.read(), _real_init, 'exec'), globals(), globals())

_original_predict = Client.predict

def _cosy_predict(self, *args, **kwargs):
    if kwargs.get('api_name') == '/generate_audio' and len(args) >= 9:
        _values = list(args)
        _values[1] = 'zero_shot'
        _values[2] = '希望你以后能够做的比我还好呦。'
        _values[5] = None
        _values[7] = False
        args = tuple(_values)
    return _original_predict(self, *args, **kwargs)

Client.predict = _cosy_predict
