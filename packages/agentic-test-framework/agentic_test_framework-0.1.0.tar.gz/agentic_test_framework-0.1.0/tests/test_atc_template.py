"""Tests for ATC template generator"""

from pathlib import Path

import pytest
from agentic_test_framework.parser import ATCTemplateGenerator


class TestATCTemplateGenerator:
    """Test ATC template generator"""

    def test_generate_basic_template(self):
        """Test basic template generation"""
        content = ATCTemplateGenerator.generate_basic_template()

        assert "# Test Suite Name" in content
        assert "@config browser=chromium" in content
        assert "## Scenario:" in content
        assert "@tag smoke" in content

    def test_generate_login_template(self):
        """Test login template generation"""
        content = ATCTemplateGenerator.generate_login_template()

        assert "# Login Test Suite" in content
        assert "## Scenario: Successful Login" in content
        assert "## Scenario: Invalid Credentials" in content
        assert "@tag login" in content
        assert "YOUR_APP_URL" in content

    def test_generate_ecommerce_template(self):
        """Test e-commerce template generation"""
        content = ATCTemplateGenerator.generate_ecommerce_template()

        assert "# E-Commerce Test Suite" in content
        assert "## Scenario: Product Search" in content
        assert "## Scenario: Add to Cart" in content
        assert "## Scenario: Checkout Flow" in content
        assert "@tag checkout" in content

    def test_generate_api_template(self):
        """Test API template generation"""
        content = ATCTemplateGenerator.generate_api_testing_template()

        assert "# API Integration Test Suite" in content
        assert "## Scenario: User Registration Flow" in content
        assert "@tag registration" in content

    def test_create_file_basic(self, tmp_path):
        """Test creating basic template file"""
        output_path = tmp_path / "test.atc"

        result = ATCTemplateGenerator.create_file(str(output_path), "basic")

        assert result is True
        assert output_path.exists()

        content = output_path.read_text()
        assert "# Test Suite Name" in content

    def test_create_file_with_template_type(self, tmp_path):
        """Test creating file with specific template"""
        output_path = tmp_path / "login.atc"

        result = ATCTemplateGenerator.create_file(str(output_path), "login")

        assert result is True
        assert output_path.exists()

        content = output_path.read_text()
        assert "# Login Test Suite" in content

    def test_create_file_without_extension(self, tmp_path):
        """Test creating file without .atc extension"""
        output_path = tmp_path / "test"

        result = ATCTemplateGenerator.create_file(str(output_path), "basic")

        assert result is True
        assert Path(f"{output_path}.atc").exists()

    def test_create_file_exists_no_overwrite(self, tmp_path):
        """Test creating file when it exists without overwrite"""
        output_path = tmp_path / "test.atc"
        output_path.write_text("existing content")

        result = ATCTemplateGenerator.create_file(str(output_path), "basic", overwrite=False)

        assert result is False
        assert output_path.read_text() == "existing content"

    def test_create_file_exists_with_overwrite(self, tmp_path):
        """Test creating file when it exists with overwrite"""
        output_path = tmp_path / "test.atc"
        output_path.write_text("existing content")

        result = ATCTemplateGenerator.create_file(str(output_path), "basic", overwrite=True)

        assert result is True
        content = output_path.read_text()
        assert "# Test Suite Name" in content
        assert "existing content" not in content

    def test_create_file_creates_directories(self, tmp_path):
        """Test creating file in non-existent directory"""
        output_path = tmp_path / "nested" / "dir" / "test.atc"

        result = ATCTemplateGenerator.create_file(str(output_path), "basic")

        assert result is True
        assert output_path.exists()
        assert output_path.parent.exists()

    def test_all_templates_are_valid_atc(self):
        """Test that all templates are valid ATC format"""
        from agentic_test_framework.parser import ATCParser

        parser = ATCParser()
        templates = ["basic", "login", "ecommerce", "api"]

        for template_type in templates:
            if template_type == "basic":
                content = ATCTemplateGenerator.generate_basic_template()
            elif template_type == "login":
                content = ATCTemplateGenerator.generate_login_template()
            elif template_type == "ecommerce":
                content = ATCTemplateGenerator.generate_ecommerce_template()
            elif template_type == "api":
                content = ATCTemplateGenerator.generate_api_testing_template()

            # Should parse without errors
            suite = parser.parse_content(content)
            assert suite.name
            assert len(suite.scenarios) > 0
