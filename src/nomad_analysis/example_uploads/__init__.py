from nomad.config.models.plugins import ExampleUploadEntryPoint

auto_xrd_example_upload = ExampleUploadEntryPoint(
    title='Auto XRD example upload',
    category='Examples',
    description='This example upload contains a notebook and instructions on how to '
    'train an [XRD Auto Analyzer](https://github.com/njszym/XRD-AutoAnalyzer) model '
    'in NORTH and save it as an entry.',
    path='example_uploads/auto_xrd/',
)
