from nomad.config.models.plugins import SchemaPackageEntryPoint


class AutoXRDSchemaPackageEntryPoint(SchemaPackageEntryPoint):
    """
    Schema for training Auto XRD models and running Auto XRD analysis.
    """

    def load(self):
        from nomad_analysis.auto_xrd.schema import m_package

        return m_package


schema = AutoXRDSchemaPackageEntryPoint(
    name='Auto XRD',
    description='Schema for training Auto XRD models and running Auto XRD analysis.',
)
