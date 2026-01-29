Organization:
- Organize tests by domain/feature in appropriate directory structure
- Group related tests by behavior using descriptive test methods
- Use `pytest` style tests (no classes)

Naming:
- Name test methods with `should` prefix describing behavior
- Use descriptive names for test helper methods
- Follow Given-When-Then pattern in method names

Test Structure:
- Extract test steps into descriptive methods
- Use `givenXxx()` for test setup
- Use `whenXxx()` for executing behavior
- Use `thenXxx()` for assertions
- Keep assertions focused and minimal

Test Data:
- Use stubs and fakes, never mocks
- Create test data in setup methods
- Use factories for test entities

Test Quality:
- Test behaviors not implementation details
- Test both success and failure paths
- Keep tests independent and deterministic
- Test edge cases and error conditions

Testing strategy:
- Unit tests should use test doubles and focus on business logic
- Integration tests should use real dependencies and test the adapter without business logic
- End to End tests should test that business code and infrastructure code is wired properly and focus on happy path, with all real dependencies