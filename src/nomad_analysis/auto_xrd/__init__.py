from nomad.config.models.plugins import SchemaPackageEntryPoint
from pydantic import Field


class NewSchemaPackageEntryPoint(SchemaPackageEntryPoint):
    parameter: int = Field(0, description='Custom configuration parameter')

    def load(self):
        from nomad_analysis.auto_xrd.auto_xrd import m_package

        return m_package


auto_xrd = NewSchemaPackageEntryPoint(
    name='auto_xrd',
    description='New schema package entry point configuration.',
)


class XRDAnalaysisSchemaPackageEntryPoint(SchemaPackageEntryPoint):
    parameter: int = Field(0, description='Custom configuration parameter')

    def load(self):
        from nomad_analysis.auto_xrd.auto_xrd_analysis import m_package

        return m_package


auto_xrd_analysis = XRDAnalaysisSchemaPackageEntryPoint(
    name='auto_xrd_analysis',
    description='New schema package entry point configuration.',
)
