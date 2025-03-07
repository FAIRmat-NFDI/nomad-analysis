from nomad.config.models.plugins import AppEntryPoint

from nomad_analysis.apps.auto_xrd_models_app import auto_xrd_models_app

app_entry_point = AppEntryPoint(
    name='Auto XRD Models',
    description='Search auto XRD models',
    app=auto_xrd_models_app,
)
