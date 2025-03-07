from nomad.datamodel.data import ArchiveSection, Schema
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.datamodel.results import DiffractionPattern
from nomad.metainfo import Quantity, SchemaPackage, SubSection

m_package = SchemaPackage()


class AnalysisSettings(ArchiveSection):
    """
    A schema for the settings of the XRD-AutoAnalyzer analysis.
    """

    xrd_model = Quantity(
        type=str,
        description='The path to the XRD model file.',
        shape=[],
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.FileEditQuantity,
        ),
    )

    pdf_model = Quantity(
        type=str,
        description='The path to the PDF model file.',
        shape=[],
        a_eln=ELNAnnotation(
            component=ELNComponentEnum.FileEditQuantity,
        ),
    )

    structure_references_directory = Quantity(
        type=str,
        description='The path to the folder containing the reference structures.',
        shape=[],
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )

    patterns_folder_directory = Quantity(
        type=str,
        description='The path to the folder containing the XRD patterns.',
        shape=[],
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )

    max_phases = Quantity(
        type=int,
        description='The maximum number of phases to consider.',
        shape=[],
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )

    cutoff_intensity = Quantity(
        type=float,
        description='The cutoff intensity for peak detection.',
        shape=[],
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )

    min_confidence = Quantity(
        type=float,
        description='The minimum confidence level for peak detection.',
        shape=[],
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )

    wavelength = Quantity(
        type=str,
        description='The X-ray wavelength.',
        shape=[],
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )

    unknown_threshold = Quantity(
        type=float,
        description='The threshold for unknown peaks.',
        shape=[],
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )

    show_reduced = Quantity(
        type=bool,
        description='Whether to show reduced patterns.',
        shape=[],
        a_eln=ELNAnnotation(component=ELNComponentEnum.BoolEditQuantity),
    )

    include_pdf = Quantity(
        type=bool,
        description='Whether to include PDF analysis.',
        shape=[],
        a_eln=ELNAnnotation(component=ELNComponentEnum.BoolEditQuantity),
    )

    parallel = Quantity(
        type=bool,
        description='Whether to use parallel processing.',
        shape=[],
        a_eln=ELNAnnotation(component=ELNComponentEnum.BoolEditQuantity),
    )

    raw = Quantity(
        type=bool,
        description='Whether to show raw patterns.',
        shape=[],
        a_eln=ELNAnnotation(component=ELNComponentEnum.BoolEditQuantity),
    )

    show_individual = Quantity(
        type=bool,
        description='Whether to show individual predictions.',
        shape=[],
        a_eln=ELNAnnotation(component=ELNComponentEnum.BoolEditQuantity),
    )

    min_angle = Quantity(
        type=float,
        description='The minimum angle value.',
        shape=[],
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )

    max_angle = Quantity(
        type=float,
        description='The maximum angle value.',
        shape=[],
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )


class PhaseDiffractionPattern(DiffractionPattern):
    name = Quantity(
        type=str,
        description='The formula of the phase and the space group.',
        shape=[],
        a_eln=ELNAnnotation(component=ELNComponentEnum.StringEditQuantity),
    )

    structure_file = Quantity(
        type=str,
        description='The path to the structure file.',
        shape=[],
        a_eln=ELNAnnotation(component=ELNComponentEnum.FileEditQuantity),
    )

    confidence = Quantity(
        type=float,
        description='The confidence level of the phase identification.',
        shape=[],
        a_eln=ELNAnnotation(component=ELNComponentEnum.NumberEditQuantity),
    )


class AnalyzedPattern(DiffractionPattern):
    identified_phases = SubSection(
        sub_section=PhaseDiffractionPattern.m_def,
        repeats=True,
    )


class AutoXRDAnalysis(Schema):
    """
    A schema for analysing XRD data with the
    [XRD-AutoAnalyzer](https://github.com/njszym/XRD-AutoAnalyzer) model.
    """

    auto_xrd_model_entry = Quantity(
        type=ArchiveSection,
        description='The entry name of the XRD-AutoAnalyzer model.',
        shape=[],
        a_eln=ELNAnnotation(component=ELNComponentEnum.ReferenceEditQuantity),
    )

    xrd_measurements_entry = Quantity(
        type=ArchiveSection,
        description='The entry name of the XRD measurements.',
        shape=[],
        a_eln=ELNAnnotation(component=ELNComponentEnum.ReferenceEditQuantity),
    )

    analysis_settings = SubSection(
        sub_section=AnalysisSettings.m_def,
    )

    analyzed_pattern = SubSection(
        sub_section=AnalyzedPattern.m_def,
        repeats=True,
    )


m_package.__init_metainfo__()
