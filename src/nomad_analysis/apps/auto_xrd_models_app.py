import yaml

auto_xrd_models_app = yaml.safe_load(
    """
label: Auto XRD Models
path: auto-xrd-models
category: Use Cases
description: Search auto XRD models
readme: 'This page allows you to search **auto XRD models entries** based
on model parameters and reference structures used to train the model.'
filters:
  include:
    - '*#nomad_auto_xrd.schema_packages.auto_xrd.AutoXRDModel'
  exclude:
    - mainfile
    - entry_name
    - combine
filters_locked:
  sections: nomad_auto_xrd.schema_packages.auto_xrd.AutoXRDModel
pagination:
  order_by: results.properties.optoelectronic.solar_cell.efficiency
search_syntaxes:
  exclude:
    - free_text
columns:
  selected:
    - results.material.elements
    - data.min_angle#nomad_auto_xrd.schema_packages.auto_xrd.AutoXRDModel
    - data.max_angle#nomad_auto_xrd.schema_packages.auto_xrd.AutoXRDModel
    - data.num_epochs#nomad_auto_xrd.schema_packages.auto_xrd.AutoXRDModel
    - entry_name
  options:
    data.min_angle#nomad_auto_xrd.schema_packages.auto_xrd.AutoXRDModel:
      label: Minimum 2 theta
    data.max_angle#nomad_auto_xrd.schema_packages.auto_xrd.AutoXRDModel:
      label: Maximum 2 theta
    data.num_epochs#nomad_auto_xrd.schema_packages.auto_xrd.AutoXRDModel:
      label: Number of epochs
    results.material.chemical_formula_descriptive: {label: Descriptive formula}
    references: {}
    results.material.elements:
      label: Chemical Space
    results.material.chemical_formula_iupac:
      label: Formula
    results.material.structural_type: {}
    results.eln.sections: {}
    results.eln.methods: {}
    entry_name: {label: Name}
    entry_type: {}
    mainfile: {}
    upload_create_time: {label: Upload time}
    authors: {}
    comment: {}
    datasets: {}
    published: {label: Access}
filter_menus:
  options:
    material:
      label: Material
    elements:
      label: Elements / Formula
      level: 1
      size: xl
    structure:
      label: Structure / Symmetry
      level: 1
    custom_quantities:
      label: User Defined Quantities
      size: l
    author:
      label: Author / Origin / Dataset
      size: m
    metadata:
      label: Visibility / IDs / Schema
    optimade:
      label: Optimade
      size: m
dashboard:
  widgets:
    - layout:
        xxl: {minH: 8, minW: 12, h: 9, w: 13, y: 0, x: 0}
        xl: {minH: 8, minW: 12, h: 9, w: 12, y: 0, x: 0}
        lg: {minH: 8, minW: 12, h: 8, w: 12, y: 0, x: 0}
        md: {minH: 8, minW: 12, h: 8, w: 12, y: 0, x: 0}
        sm: {minH: 8, minW: 12, h: 8, w: 12, y: 0, x: 0}
      type: periodictable
      scale: linear
      quantity: results.material.elements

    - type: terms
      showinput: true
      scale: linear
      quantity: results.material.topology.chemical_formula_iupac
      layout:
        xxl: {minH: 3, minW: 3, h: 9, w: 6, y: 0, x: 13}
        xl: {minH: 3, minW: 3, h: 9, w: 5, y: 0, x: 12}
        lg: {minH: 3, minW: 3, h: 8, w: 6, y: 0, x: 12}
        md: {minH: 3, minW: 3, h: 8, w: 3, y: 0, x: 12}
        sm: {minH: 3, minW: 3, h: 7, w: 4, y: 11, x: 8}

    - type: histogram
      autorange: false
      nbins: 30
      y:
        scale: linear
      x:
        quantity: data.num_epochs#nomad_auto_xrd.schema_packages.auto_xrd.AutoXRDModel
        title: Number of epochs
      title: Number of epochs
      layout:
        xxl: {minH: 3, minW: 3, h: 3, w: 8, y: 6, x: 25}
        xl: {minH: 3, minW: 3, h: 3, w: 8, y: 6, x: 22}
        lg: {minH: 3, minW: 3, h: 3, w: 8, y: 8, x: 16}
        md: {minH: 3, minW: 3, h: 3, w: 4, y: 8, x: 8}
        sm: {minH: 3, minW: 3, h: 3, w: 8, y: 11, x: 0}

    - type: histogram
      autorange: false
      nbins: 30
      y:
        scale: linear
      x:
        quantity: data.max_angle#nomad_auto_xrd.schema_packages.auto_xrd.AutoXRDModel
        title: Maximum 2 theta
      title: Maximum 2 theta
      layout:
        xxl: {minH: 3, minW: 3, h: 3, w: 8, y: 0, x: 25}
        xl: {minH: 3, minW: 3, h: 3, w: 8, y: 3, x: 22}
        lg: {minH: 3, minW: 3, h: 3, w: 8, y: 8, x: 8}
        md: {minH: 3, minW: 3, h: 3, w: 4, y: 8, x: 4}
        sm: {minH: 3, minW: 3, h: 3, w: 6, y: 8, x: 6}

    - type: histogram
      autorange: false
      nbins: 30
      y:
        scale: linear
      x:
        quantity: data.min_angle#nomad_auto_xrd.schema_packages.auto_xrd.AutoXRDModel
        title: Minimum 2 theta
      title: Minimum 2 theta
      layout:
        xxl: {minH: 3, minW: 3, h: 3, w: 8, y: 3, x: 25}
        xl: {minH: 3, minW: 3, h: 3, w: 8, y: 0, x: 22}
        lg: {minH: 3, minW: 3, h: 3, w: 8, y: 8, x: 0}
        md: {minH: 3, minW: 3, h: 3, w: 4, y: 8, x: 0}
        sm: {minH: 3, minW: 3, h: 3, w: 6, y: 8, x: 0}

    - type: terms
      scale: linear
      quantity: results.material.topology.symmetry.crystal_system
      layout:
        xxl: {minH: 3, minW: 3, h: 9, w: 6, y: 0, x: 15}
        xl: {minH: 3, minW: 3, h: 9, w: 6, y: 0, x: 15}
        lg: {minH: 3, minW: 3, h: 9, w: 6, y: 0, x: 15}
        md: {minH: 3, minW: 3, h: 8, w: 3, y: 0, x: 15}
        sm: {minH: 3, minW: 3, h: 4, w: 4, y: 14, x: 0}
"""
)
