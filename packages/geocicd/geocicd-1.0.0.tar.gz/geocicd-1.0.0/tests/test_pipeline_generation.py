#!/usr/bin/env python3
"""
Test script for Task 5: Verify pipeline generation

This script:
1. Parses example configurations
2. Generates .gitlab-ci.yml files
3. Validates YAML syntax
4. Verifies expected jobs are present
"""

import sys
import yaml
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from parser.config_parser import ConfigParser
from generator.gitlab_ci_generator import GitLabCIGenerator


def test_yaml_validity(yaml_content: str, config_name: str) -> bool:
    """Test if generated YAML is valid."""
    print(f"\n{'='*60}")
    print(f"Testing YAML validity for: {config_name}")
    print(f"{'='*60}")
    
    try:
        parsed = yaml.safe_load(yaml_content)
        print("✓ YAML is valid and parseable")
        return True
    except yaml.YAMLError as e:
        print(f"✗ YAML parsing failed: {e}")
        return False


def verify_expected_jobs(yaml_content: str, config_name: str, expected_jobs: list) -> bool:
    """Verify that expected jobs are present in the pipeline."""
    print(f"\nVerifying expected jobs...")
    
    try:
        pipeline = yaml.safe_load(yaml_content)
        
        # Get all job names (exclude special keys like workflow, stages, variables)
        special_keys = {'workflow', 'stages', 'variables', 'default', 'include'}
        job_names = [key for key in pipeline.keys() if key not in special_keys]
        
        print(f"\nFound {len(job_names)} jobs:")
        for job in sorted(job_names):
            print(f"  - {job}")
        
        # Check for expected jobs
        missing_jobs = []
        for expected in expected_jobs:
            if expected not in job_names:
                missing_jobs.append(expected)
        
        if missing_jobs:
            print(f"\n✗ Missing expected jobs:")
            for job in missing_jobs:
                print(f"  - {job}")
            return False
        else:
            print(f"\n✓ All {len(expected_jobs)} expected jobs are present")
            return True
            
    except Exception as e:
        print(f"✗ Error verifying jobs: {e}")
        return False


def verify_pipeline_structure(yaml_content: str, config_name: str) -> bool:
    """Verify pipeline has correct structure."""
    print(f"\nVerifying pipeline structure...")
    
    try:
        pipeline = yaml.safe_load(yaml_content)
        
        # Check for required sections
        required_sections = ['workflow', 'stages', 'variables']
        missing_sections = []
        
        for section in required_sections:
            if section not in pipeline:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"✗ Missing required sections: {', '.join(missing_sections)}")
            return False
        
        # Verify workflow rules
        if 'rules' not in pipeline['workflow']:
            print("✗ Workflow missing 'rules' section")
            return False
        
        # Verify stages
        stages = pipeline.get('stages', [])
        print(f"\nPipeline stages ({len(stages)}):")
        for stage in stages:
            print(f"  - {stage}")
        
        # Verify variables
        variables = pipeline.get('variables', {})
        print(f"\nGlobal variables ({len(variables)}):")
        for key, value in variables.items():
            print(f"  - {key}: {value}")
        
        print("\n✓ Pipeline structure is valid")
        return True
        
    except Exception as e:
        print(f"✗ Error verifying structure: {e}")
        return False


def test_configuration(config_file: str, expected_jobs: list) -> bool:
    """Test a single configuration file."""
    config_name = Path(config_file).stem
    
    print(f"\n{'#'*60}")
    print(f"# Testing: {config_name}")
    print(f"# Config: {config_file}")
    print(f"{'#'*60}")
    
    try:
        # Parse configuration with runtime variables
        print("\n1. Parsing configuration...")
        parser = ConfigParser(schema_path="schemas/ci-config.schema.json")
        
        # Load YAML first
        config = parser._load_yaml(config_file)
        
        # Add runtime variables for testing
        if 'defaults' not in config:
            config['defaults'] = {}
        if 'git' not in config['defaults']:
            config['defaults']['git'] = {}
        if 'component' not in config['defaults']:
            config['defaults']['component'] = {}
        
        config['defaults']['git']['branch'] = 'develop'
        config['defaults']['git']['build_number'] = '123'
        config['defaults']['component']['name'] = 'test-component'
        
        # Now parse with the added runtime variables
        config = parser.parse_dict(config)
        print(f"✓ Configuration parsed successfully")
        
        # Generate pipeline
        print("\n2. Generating GitLab CI pipeline...")
        generator = GitLabCIGenerator()
        yaml_content = generator.generate(config)
        print(f"✓ Pipeline generated ({len(yaml_content)} characters)")
        
        # Save to file
        output_file = f"generated-{config_name}.gitlab-ci.yml"
        with open(output_file, 'w') as f:
            f.write(yaml_content)
        print(f"✓ Pipeline saved to: {output_file}")
        
        # Test YAML validity
        if not test_yaml_validity(yaml_content, config_name):
            return False
        
        # Verify pipeline structure
        if not verify_pipeline_structure(yaml_content, config_name):
            return False
        
        # Verify expected jobs
        if not verify_expected_jobs(yaml_content, config_name, expected_jobs):
            return False
        
        print(f"\n{'='*60}")
        print(f"✓ ALL TESTS PASSED for {config_name}")
        print(f"{'='*60}")
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("="*60)
    print("Task 5: Verify Pipeline Generation")
    print("="*60)
    
    # Test configurations
    test_cases = [
        {
            'file': 'config/examples/simple-vue-app.yaml',
            'expected_jobs': [
                'validate:config',
                'build:frontend',
                'deploy:dev:frontend',
                'deploy:stg:frontend',
                'deploy:ese:frontend',
            ]
        },
        {
            'file': 'config/examples/java-microservices.yaml',
            'expected_jobs': [
                'validate:config',
                'build:api-gateway',
                'build:order-service',
                'build:payment-service',
                'build:notification-service',
                'quality:api-gateway',
                'quality:order-service',
            ]
        },
        {
            'file': 'config/examples/monorepo.yaml',
            'expected_jobs': [
                'validate:config',
                'detect:changes',
                'build:dashboard-frontend',
                'build:api-backend',
                'build:iot-collector',
                'build:data-processor',
            ]
        },
    ]
    
    results = []
    
    for test_case in test_cases:
        config_file = test_case['file']
        expected_jobs = test_case['expected_jobs']
        
        # Check if file exists
        if not Path(config_file).exists():
            print(f"\n✗ Configuration file not found: {config_file}")
            results.append(False)
            continue
        
        # Run test
        success = test_configuration(config_file, expected_jobs)
        results.append(success)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\nTests passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ ALL TESTS PASSED")
        return 0
    else:
        print(f"\n✗ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
