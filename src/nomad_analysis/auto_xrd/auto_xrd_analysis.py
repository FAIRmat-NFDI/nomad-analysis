from typing import (
    TYPE_CHECKING,
)

if TYPE_CHECKING:
    from nomad.datamodel.datamodel import (
        EntryArchive,
    )
    from structlog.stdlib import (
        BoundLogger,
    )

import json
import os
import time

import numpy as np
from autoXRD import spectrum_analysis, visualizer
from nomad.config import config
from nomad.datamodel.data import ArchiveSection, Schema
from nomad.datamodel.metainfo.annotations import ELNAnnotation, ELNComponentEnum
from nomad.datamodel.results import DiffractionPattern
from nomad.metainfo import Quantity, SchemaPackage, SubSection

configuration = config.get_plugin_entry_point(
    'nomad_auto_xrd.schema_packages:auto_xrd_analysis'
)

m_package = SchemaPackage()


def convert_to_serializable(obj):
    """Convert non-serializable objects like numpy arrays to serializable formats."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_serializable(item) for item in obj]
    return obj


def analyze_pattern(self, archive: 'EntryArchive', logger: 'BoundLogger') -> None:  # noqa: PLR0915
    references_folder = os.path.join(
        archive.m_context.raw_path(),
        self.analysis_settings.structure_references_directory,
    )
    print(f'References folder: {references_folder}')
    spectra_folder = os.path.join(
        archive.m_context.raw_path(), self.analysis_settings.patterns_folder_directory
    )
    max_phases = self.analysis_settings.max_phases
    cutoff_intensity = self.analysis_settings.cutoff_intensity
    min_conf = self.analysis_settings.min_confidence
    wavelength = self.analysis_settings.wavelength
    unknown_threshold = self.analysis_settings.unknown_threshold
    show_reduced = self.analysis_settings.show_reduced
    inc_pdf = self.analysis_settings.include_pdf
    parallel = self.analysis_settings.parallel
    raw = self.analysis_settings.raw
    show_indiv = self.analysis_settings.show_individual
    min_angle = self.analysis_settings.min_angle
    max_angle = self.analysis_settings.max_angle

    start = time.time()

    # Check for spectra
    if not os.path.exists(spectra_folder) or len(os.listdir(spectra_folder)) == 0:
        print(f'Please provide at least one pattern in the {spectra_folder} directory.')
        return

    results = {'XRD': {}, 'PDF': {}}

    # XRD/PDF ensemble requires all predictions
    if inc_pdf:
        final_conf = min_conf
        min_conf = 10.0

    model_path = os.path.join(
        archive.m_context.raw_path(), self.analysis_settings.xrd_model
    )

    # self.xrd_model if inc_pdf else self.pdf_model

    # Ensure temp directory exists
    if not os.path.exists('temp'):
        os.mkdir('temp')

    # Get predictions from XRD analysis
    (
        results['XRD']['filenames'],
        results['XRD']['phases'],
        results['XRD']['confs'],
        results['XRD']['backup_phases'],
        results['XRD']['scale_factors'],
        results['XRD']['reduced_spectra'],
    ) = spectrum_analysis.main(
        spectra_folder,
        references_folder,
        max_phases,
        cutoff_intensity,
        min_conf,
        wavelength,
        min_angle,
        max_angle,
        parallel,
        model_path,
        is_pdf=False,
    )

    if inc_pdf:
        # Get predictions from PDF analysis
        model_path = self.pdf_model
        (
            results['PDF']['filenames'],
            results['PDF']['phases'],
            results['PDF']['confs'],
            results['PDF']['backup_phases'],
            results['PDF']['scale_factors'],
            results['PDF']['reduced_spectra'],
        ) = spectrum_analysis.main(
            spectra_folder,
            references_folder,
            max_phases,
            cutoff_intensity,
            min_conf,
            wavelength,
            min_angle,
            max_angle,
            parallel,
            model_path,
            is_pdf=True,
        )

        # Merge results
        results['Merged'] = spectrum_analysis.merge_results(
            results, final_conf, max_phases
        )
    else:
        results['Merged'] = results['XRD']

    # Process results
    for idx, (
        spectrum_fname,
        phase_set,
        confidence,
        backup_set,
        heights,
        final_spectrum,
    ) in enumerate(
        zip(
            results['Merged']['filenames'],
            results['Merged']['phases'],
            results['Merged']['confs'],
            results['Merged']['backup_phases'],
            results['Merged']['scale_factors'],
            results['Merged']['reduced_spectra'],
        )
    ):
        # Display phase ID info
        print(f'Filename: {spectrum_fname}')
        print(f'Predicted phases: {phase_set}')
        print(f'Confidence: {confidence}')

        # Check for unknown peaks
        if len(phase_set) > 0 and 'None' not in phase_set:
            remaining_I = max(final_spectrum)
            if remaining_I > unknown_threshold:
                print(
                    f'WARNING: some peaks (I ~ {int(remaining_I)}%) were not identified.'  # noqa: E501
                )
        else:
            print('WARNING: no phases were identified')
            continue

        # Show backup predictions
        if show_indiv:
            print(f"XRD predicted phases: {results['XRD']['phases'][idx]}")
            print(f"XRD confidence: {results['XRD']['confs'][idx]}")
            if inc_pdf:
                print(f"PDF predicted phases: {results['PDF']['phases'][idx]}")
                print(f"PDF confidence: {results['PDF']['confs'][idx]}")

        # Plot the results
        phasenames = [f'{phase}.cif' for phase in phase_set]
        visualizer.main(
            spectra_folder,
            spectrum_fname,
            phasenames,
            heights,
            final_spectrum,
            min_angle,
            max_angle,
            wavelength,
            save=False,
            show_reduced=show_reduced,
            inc_pdf=inc_pdf,
            plot_both=False,
            raw=raw,
        )

    end = time.time()
    print(f'Total time: {round(end - start, 1)} sec')

    # Convert results to a JSON serializable format
    serializable_results = convert_to_serializable(results)

    # Save the results dictionary as a JSON file
    results_file = 'results.json'
    with open(results_file, 'w') as f:
        json.dump(serializable_results, f, indent=4)
    print(f'Results saved to {results_file}')


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

    def normalize(self, archive, logger):
        super().normalize(archive, logger)


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

    def normalize(self, archive, logger):
        super().normalize(archive, logger)


class AnalyzedPattern(DiffractionPattern):
    identified_phases = SubSection(
        sub_section=PhaseDiffractionPattern.m_def,
        repeats=True,
    )

    def normalize(self, archive, logger):
        super().normalize(archive, logger)


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

    def normalize(self, archive, logger):
        super().normalize(archive, logger)
        # use the normalization function defined above
        print('Normalizing AutoXRDAnalysis')
        if self.auto_xrd_model_entry is not None:
            if self.analysis_settings is not None:
                analyze_pattern(self, archive, logger)


m_package.__init_metainfo__()
