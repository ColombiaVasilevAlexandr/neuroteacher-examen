try:
    import gradio_client
    _original_predict = gradio_client.Client.predict

    def _patched_predict(self, *args, **kwargs):
        if kwargs.get('api_name') == '/generate_audio' and len(args) >= 9:
            values = list(args)
            values[1] = 'zero_shot'
            values[2] = '希望你以后能够做的比我还好呦。'
            values[5] = None
            values[7] = 'False'
            args = tuple(values)
        return _original_predict(self, *args, **kwargs)

    gradio_client.Client.predict = _patched_predict
except Exception:
    pass
