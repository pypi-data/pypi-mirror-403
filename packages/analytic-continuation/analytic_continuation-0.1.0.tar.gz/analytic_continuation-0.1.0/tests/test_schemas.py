"""Tests for the schemas submodule."""

import pytest
from analytic_continuation.schemas import (
    get_schema,
    get_config,
    get_example,
    list_schemas,
    list_configs,
    list_examples,
    SchemaNotFoundError,
)


class TestGetSchema:
    """Tests for get_schema function."""

    def test_load_types_schema(self):
        """Test loading the types.json schema."""
        schema = get_schema('types')
        assert isinstance(schema, dict)
        assert 'Complex' in schema
        assert 'SplinePoint' in schema
        assert 'LaurentMap' in schema

    def test_load_function_contracts_schema(self):
        """Test loading the function_contracts.json schema."""
        schema = get_schema('function_contracts')
        assert isinstance(schema, dict)
        assert 'fitLaurentMapFromSplineExport' in schema
        assert 'checkFHolomorphicOnAnnulusImage' in schema
        assert 'invertZ' in schema
        assert 'computeComposition' in schema

    def test_load_schema_with_extension(self):
        """Test loading schema with explicit .json extension."""
        schema = get_schema('types.json')
        assert isinstance(schema, dict)
        assert 'Complex' in schema

    def test_schema_not_found(self):
        """Test that SchemaNotFoundError is raised for non-existent schema."""
        with pytest.raises(SchemaNotFoundError) as exc_info:
            get_schema('nonexistent_schema')
        assert 'nonexistent_schema' in str(exc_info.value)
        assert 'Available' in str(exc_info.value)


class TestGetConfig:
    """Tests for get_config function."""

    def test_load_pipeline_config(self):
        """Test loading the pipeline_config.json config."""
        config = get_config('pipeline_config')
        assert isinstance(config, dict)
        assert 'pipeline' in config
        assert config['pipeline'] == 'laurent_reflection_composition_v1'
        assert 'fitLaurentMap' in config
        assert 'fHolomorphicCheck' in config
        assert 'invertZ' in config

    def test_config_has_expected_structure(self):
        """Test that pipeline config has expected nested structure."""
        config = get_config('pipeline_config')
        fit_config = config['fitLaurentMap']
        assert 'degree' in fit_config
        assert 'N_min' in fit_config['degree']
        assert 'N_max' in fit_config['degree']
        assert fit_config['degree']['N_min'] == 6
        assert fit_config['degree']['N_max'] == 64

    def test_config_not_found(self):
        """Test that SchemaNotFoundError is raised for non-existent config."""
        with pytest.raises(SchemaNotFoundError) as exc_info:
            get_config('nonexistent_config')
        assert 'nonexistent_config' in str(exc_info.value)


class TestGetExample:
    """Tests for get_example function."""

    def test_load_spline_export_example(self):
        """Test loading the spline_export.sample.json example."""
        example = get_example('spline_export.sample')
        assert isinstance(example, dict)
        assert 'version' in example
        assert 'timestamp' in example
        assert 'controlPoints' in example
        assert 'spline' in example
        assert 'adaptivePolyline' in example

    def test_example_has_valid_spline_data(self):
        """Test that example has valid spline structure."""
        example = get_example('spline_export.sample')
        assert example['version'] == '1.0'
        assert example['closed'] is True
        assert len(example['controlPoints']) > 0
        assert len(example['spline']) > 0
        # Check point structure
        point = example['controlPoints'][0]
        assert 'index' in point
        assert 'x' in point
        assert 'y' in point

    def test_example_not_found(self):
        """Test that SchemaNotFoundError is raised for non-existent example."""
        with pytest.raises(SchemaNotFoundError) as exc_info:
            get_example('nonexistent_example')
        assert 'nonexistent_example' in str(exc_info.value)


class TestListFunctions:
    """Tests for list_* functions."""

    def test_list_schemas(self):
        """Test listing available schemas."""
        schemas = list_schemas()
        assert isinstance(schemas, list)
        assert 'types' in schemas
        assert 'function_contracts' in schemas
        # Should be sorted
        assert schemas == sorted(schemas)

    def test_list_configs(self):
        """Test listing available configs."""
        configs = list_configs()
        assert isinstance(configs, list)
        assert 'pipeline_config' in configs
        # Should be sorted
        assert configs == sorted(configs)

    def test_list_examples(self):
        """Test listing available examples."""
        examples = list_examples()
        assert isinstance(examples, list)
        assert 'spline_export.sample' in examples
        # Should be sorted
        assert examples == sorted(examples)


class TestValidate:
    """Tests for validate function."""

    def test_validate_requires_jsonschema(self):
        """Test that validate works when jsonschema is available."""
        # This test will pass if jsonschema is installed
        # or raise ImportError if not (which is expected behavior)
        from analytic_continuation.schemas import validate

        try:
            # Try to validate a simple dict against types schema
            valid_complex = {'re': 1.0, 'im': 2.0}
            # The validation is structural, not type-based
            result = validate(valid_complex, 'types')
            assert result is True
        except ImportError:
            # jsonschema not installed - this is expected in minimal installs
            pytest.skip("jsonschema not installed")


class TestSchemaContents:
    """Tests for schema content integrity."""

    def test_types_schema_complex_definition(self):
        """Test Complex type definition in types schema."""
        schema = get_schema('types')
        complex_type = schema['Complex']
        assert complex_type['re'] == 'float64'
        assert complex_type['im'] == 'float64'

    def test_types_schema_laurent_map_definition(self):
        """Test LaurentMap type definition in types schema."""
        schema = get_schema('types')
        laurent_map = schema['LaurentMap']
        assert 'N' in laurent_map
        assert 'a0' in laurent_map
        assert 'a' in laurent_map
        assert 'b' in laurent_map
        assert laurent_map['N'] == 'int'
        assert laurent_map['a0'] == 'Complex'

    def test_function_contracts_invert_z(self):
        """Test invertZ function contract."""
        contracts = get_schema('function_contracts')
        invert_z = contracts['invertZ']
        assert 'inputs' in invert_z
        assert 'outputs' in invert_z
        assert 'zQuery' in invert_z['inputs']
        assert 'laurentMap' in invert_z['inputs']
        assert 'converged' in invert_z['outputs']
        assert 'zeta' in invert_z['outputs']

    def test_pipeline_config_sampling(self):
        """Test pipeline config sampling parameters."""
        config = get_config('pipeline_config')
        sampling = config['fitLaurentMap']['sampling']
        assert sampling['method'] == 'arc_length_resample'
        assert sampling['m_samples'] == 2048

    def test_example_stats(self):
        """Test example file has correct stats."""
        example = get_example('spline_export.sample')
        stats = example['stats']
        assert stats['controlPointCount'] == 7
        assert stats['splinePointCount'] == 211
        assert stats['adaptivePointCount'] == 23


class TestImportFromPackage:
    """Tests for importing schema utilities from the main package."""

    def test_import_from_analytic_continuation(self):
        """Test that schema utilities can be imported from main package."""
        from analytic_continuation import (
            get_schema,
            get_config,
            get_example,
            list_schemas,
            list_configs,
            list_examples,
            SchemaNotFoundError,
        )

        # Verify imports work
        assert callable(get_schema)
        assert callable(get_config)
        assert callable(get_example)
        assert callable(list_schemas)
        assert callable(list_configs)
        assert callable(list_examples)
        assert issubclass(SchemaNotFoundError, Exception)

    def test_schema_utilities_in_package_all(self):
        """Test that schema utilities are in package __all__."""
        import analytic_continuation

        all_exports = analytic_continuation.__all__
        assert 'get_schema' in all_exports
        assert 'get_config' in all_exports
        assert 'get_example' in all_exports
        assert 'list_schemas' in all_exports
        assert 'list_configs' in all_exports
        assert 'list_examples' in all_exports
        assert 'SchemaNotFoundError' in all_exports
