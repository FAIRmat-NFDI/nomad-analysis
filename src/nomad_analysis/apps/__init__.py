from nomad.config.models.plugins import AppEntryPoint

from nomad_analysis.apps.auto_xrd import models_app

auto_xrd_models_app = AppEntryPoint(
    name='Auto XRD Models',
    description='Search auto XRD models',
    app=models_app,
)
