from nomad.config.models.plugins import SchemaPackageEntryPoint


class NewSchemaPackageEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from nomad_analysis.auto_xrd.auto_xrd import m_package

        return m_package


class XRDAnalaysisSchemaPackageEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from nomad_analysis.auto_xrd.auto_xrd_analysis import m_package

        return m_package


class AnalysisSchemaPackageEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from nomad_analysis.auto_xrd.analysis import m_package

        return m_package


class TrainingSchemaPackageEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from nomad_analysis.auto_xrd.training import m_package

        return m_package


auto_xrd = NewSchemaPackageEntryPoint(
    name='auto_xrd',
    description='New schema package entry point configuration.',
)
auto_xrd_analysis = XRDAnalaysisSchemaPackageEntryPoint(
    name='auto_xrd_analysis',
    description='New schema package entry point configuration.',
)
analysis_schema = AnalysisSchemaPackageEntryPoint(
    name='Auto XRD Inference Schema',
    description='Schema for performing Auto XRD analysis.',
)
training_schema = TrainingSchemaPackageEntryPoint(
    name='Auto XRD Training Schema',
    description='Schema for training Auto XRD models.',
)
