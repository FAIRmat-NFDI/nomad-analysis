def test_importing_app():
    # this will raise an exception if pydantic model validation fails for th app
    from nomad_analysis.apps import auto_xrd_models_app

    assert auto_xrd_models_app.app.label == 'Auto XRD Models'
