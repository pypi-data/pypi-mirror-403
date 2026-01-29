import unittest
import os
import sys
import yaml
from yaml_config_manager import load_config, Config

class TestYamlConfigManager(unittest.TestCase):
    def setUp(self):
        self.config_file = 'tests/temp_test_config.yaml'
        self.data = {
            'section': {
                'param': 1.0,
                'subparam': 'original'
            },
            'learning_rate': 1e-4,
            'features': {
                'enabled': False
            }
        }
        with open(self.config_file, 'w') as f:
            yaml.dump(self.data, f)

    def tearDown(self):
        if os.path.exists(self.config_file):
            os.remove(self.config_file)

    def test_load_config_basic(self):
        config = load_config(self.config_file, args=[])
        self.assertEqual(config.section.param, 1.0)
        self.assertEqual(config.learning_rate, 0.0001)
        self.assertIsInstance(config.learning_rate, float)

    def test_scientific_notation(self):
        with open('tests/sci_config.yaml', 'w') as f:
            f.write("val1: 1e-4\nval2: 1.0E-5\n")
        
        config = load_config('tests/sci_config.yaml', args=[])
        self.assertEqual(config.val1, 0.0001)
        self.assertEqual(config.val2, 0.00001)
        self.assertIsInstance(config.val1, float)
        os.remove('tests/sci_config.yaml')

    def test_cli_override_equals_style(self):
        # --key=value
        args = ['--config', self.config_file, '--section.param=2.5', '--section.subparam=changed']
        config = load_config(args=args)
        self.assertEqual(config.section.param, 2.5)
        self.assertEqual(config.section.subparam, 'changed')

    def test_cli_override_space_style(self):
        # --key value
        args = ['--config', self.config_file, '--section.param', '3.5', '--section.subparam', 'space_changed']
        config = load_config(args=args)
        self.assertEqual(config.section.param, 3.5)
        self.assertEqual(config.section.subparam, 'space_changed')

    def test_cli_override_mixed_style(self):
        # Mixed --key=value and --key value
        args = ['--config', self.config_file, '--section.param=4.5', '--features.enabled', 'true']
        config = load_config(args=args)
        self.assertEqual(config.section.param, 4.5)
        self.assertTrue(config.features.enabled)

    def test_cli_override_quotes_simulated(self):
        # Shells handle quotes before they reach python, so "value with spaces" comes in as a single arg
        args = ['--config', self.config_file, '--section.subparam', 'value with spaces']
        config = load_config(args=args)
        self.assertEqual(config.section.subparam, 'value with spaces')

        args2 = ['--config', self.config_file, '--section.subparam=value with spaces']
        config = load_config(args=args2)
        self.assertEqual(config.section.subparam, 'value with spaces')

    def test_boolean_flags(self):
        # --flag (implicit true)
        args = ['--config', self.config_file, '--new_flag']
        config = load_config(args=args)
        self.assertTrue(config.new_flag)

    def test_boolean_conversion(self):
        # yes/no/on/off
        args = ['--config', self.config_file, '--v1', 'yes', '--v2', 'no', '--v3', 'on', '--v4', 'OFF']
        config = load_config(args=args)
        self.assertTrue(config.v1)
        self.assertFalse(config.v2)
        self.assertTrue(config.v3)
        self.assertFalse(config.v4)

    def test_dotted_notation_access(self):
        config = load_config(self.config_file, args=[])
        self.assertEqual(config.section.subparam, 'original')
        
    def test_missing_key_attribute_error(self):
        config = load_config(self.config_file, args=[])
        with self.assertRaises(AttributeError):
            _ = config.non_existent_section

    def test_deeply_nested_creation(self):
        args = ['--config', self.config_file, '--deep.nested.value', '100']
        config = load_config(args=args)
        self.assertEqual(config.deep.nested.value, 100)

if __name__ == '__main__':
    unittest.main()
