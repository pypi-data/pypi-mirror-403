"""ATC file template generator"""

from pathlib import Path
from typing import Optional


class ATCTemplateGenerator:
    """Generate ATC file templates"""
    
    @staticmethod
    def generate_basic_template() -> str:
        """Generate a basic ATC template"""
        return """# Test Suite Name

Description: Brief description of what this test suite does

@config browser=chromium
@config headless=false

## Scenario: First Test
@tag smoke
@id TC-001
@objective Verify the homepage loads correctly
@preconditions Application is reachable
@expected Page shows the Example Domain content
@postconditions Browser remains on the homepage
@reference REQ-BASIC-001

Go to example.com
Verify page contains 'Example Domain'
Take a screenshot

## Scenario: Second Test
@id TC-002
@objective Describe the goal of this test
@preconditions Describe required preconditions
@expected Describe the expected outcome
@postconditions Describe the state after execution
@reference REQ-BASIC-002

Add your test steps here...
"""
    
    @staticmethod
    def generate_login_template() -> str:
        """Generate a login flow template"""
        return """# Login Test Suite

Description: Test suite for user authentication flows

@config browser=chromium
@config headless=false

## Scenario: Successful Login
@tag smoke
@tag login
@id TC-LOGIN-001
@objective Validate successful login with valid credentials
@preconditions User account exists and is active
@expected User is logged in and sees the dashboard
@postconditions User remains logged in
@reference REQ-LOGIN-001

Go to YOUR_APP_URL/login
Type 'YOUR_USERNAME' into username field
Type 'YOUR_PASSWORD' into password field
Click login button
Verify page contains 'Welcome'
Take a screenshot named 'successful_login'

## Scenario: Invalid Credentials
@tag login
@tag negative
@id TC-LOGIN-002
@objective Validate login failure with invalid credentials
@preconditions User account exists
@expected Error message indicates invalid credentials
@postconditions User is not logged in
@reference REQ-LOGIN-002

Go to YOUR_APP_URL/login
Type 'invalid_user' into username field
Type 'wrong_password' into password field
Click login button
Verify page contains 'Invalid credentials'
Take a screenshot

## Scenario: Empty Form Validation
@tag login
@tag validation
@id TC-LOGIN-003
@objective Validate required field messages on empty form
@preconditions Login page is accessible
@expected Required field messages are shown
@postconditions User remains on login page
@reference REQ-LOGIN-003

Go to YOUR_APP_URL/login
Click login button
Verify page contains 'required'
"""
    
    @staticmethod
    def generate_ecommerce_template() -> str:
        """Generate an e-commerce flow template"""
        return """# E-Commerce Test Suite

Description: Test suite for shopping and checkout flows

@config browser=chromium
@config headless=false

## Scenario: Product Search
@tag smoke
@tag search
@id TC-SHOP-001
@objective Validate product search returns results
@preconditions Shop is reachable and contains products
@expected Results list is shown
@postconditions User remains on results page
@reference REQ-SHOP-001

Go to YOUR_SHOP_URL
Type 'product name' into search box
Click search button
Verify page contains 'results'
Take a screenshot

## Scenario: Add to Cart
@tag cart
@id TC-SHOP-002
@objective Validate adding a product to the cart
@preconditions Shop is reachable and contains products
@expected Cart contains the selected product
@postconditions Cart state is updated
@reference REQ-SHOP-002

Go to YOUR_SHOP_URL
Click first product
Click 'Add to Cart' button
Verify page contains 'Added to cart'
Click cart icon
Verify page contains product name

## Scenario: Checkout Flow
@tag checkout
@tag critical
@id TC-SHOP-003
@objective Validate checkout flow to payment step
@preconditions Cart has at least one item
@expected Payment step is displayed
@postconditions Cart remains intact if checkout not completed
@reference REQ-SHOP-003

Go to YOUR_SHOP_URL/cart
Click 'Checkout' button
Type 'customer@email.com' into email field
Type '123 Main St' into address field
Click 'Continue' button
Verify page contains 'Payment'
"""
    
    @staticmethod
    def generate_api_testing_template() -> str:
        """Generate an API/integration testing template"""
        return """# API Integration Test Suite

Description: Test suite for API endpoints and integrations

@config browser=chromium
@config headless=true

## Scenario: User Registration Flow
@tag smoke
@tag registration
@id TC-API-001
@objective Validate user registration flow
@preconditions Registration page is accessible
@expected Registration succeeds and user reaches dashboard
@postconditions User account is created
@reference REQ-API-001

Go to YOUR_APP_URL/register
Type 'newuser@example.com' into email field
Type 'SecurePass123' into password field
Type 'SecurePass123' into confirm password field
Click register button
Verify page contains 'Registration successful'
Verify URL contains 'dashboard'

## Scenario: Profile Update
@tag profile
@id TC-API-002
@objective Validate profile update saves changes
@preconditions User account exists and can log in
@expected Profile updates are saved
@postconditions User remains logged in
@reference REQ-API-002

Go to YOUR_APP_URL/login
Type 'user@example.com' into email field
Type 'password' into password field
Click login button
Click 'Profile' link
Type 'Updated Name' into name field
Click 'Save' button
Verify page contains 'Profile updated'
"""
    
    @staticmethod
    def create_file(
        output_path: str,
        template_type: str = "basic",
        overwrite: bool = False
    ) -> bool:
        """Create an ATC file from template
        
        Args:
            output_path: Path where to create the ATC file
            template_type: Type of template (basic, login, ecommerce, api)
            overwrite: Whether to overwrite existing file
            
        Returns:
            True if file was created, False if file exists and overwrite=False
        """
        path = Path(output_path)
        
        # Check if file exists
        if path.exists() and not overwrite:
            return False
        
        # Ensure .atc extension
        if not output_path.endswith('.atc'):
            path = Path(f"{output_path}.atc")
        
        # Get template content
        templates = {
            "basic": ATCTemplateGenerator.generate_basic_template(),
            "login": ATCTemplateGenerator.generate_login_template(),
            "ecommerce": ATCTemplateGenerator.generate_ecommerce_template(),
            "api": ATCTemplateGenerator.generate_api_testing_template()
        }
        
        content = templates.get(template_type, templates["basic"])
        
        # Create directory if needed
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        path.write_text(content)
        
        return True
