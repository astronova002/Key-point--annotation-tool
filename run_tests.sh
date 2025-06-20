#!/bin/bash

# Test Runner Script for GMM Annotation Tool
# This script runs both backend and frontend tests

set -e  # Exit on any error

echo "🧪 Running Comprehensive Test Suite for GMM Annotation Tool"
echo "=========================================================="

# Function to print colored output
print_status() {
    echo -e "\033[1;34m$1\033[0m"
}

print_success() {
    echo -e "\033[1;32m$1\033[0m"
}

print_error() {
    echo -e "\033[1;31m$1\033[0m"
}

print_warning() {
    echo -e "\033[1;33m$1\033[0m"
}

# Initialize counters
BACKEND_TESTS_PASSED=0
FRONTEND_TESTS_PASSED=0
TOTAL_ERRORS=0

# Backend Tests
print_status "📋 Running Backend Tests (Django/pytest)"
echo "------------------------------------------"

cd backend

# Check if virtual environment is needed
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    print_warning "No virtual environment found. Make sure dependencies are installed."
fi

# Run Django tests with coverage
print_status "Running Django Model Tests..."
if python -m pytest tests/test_models.py -v --tb=short; then
    print_success "✅ Model tests passed"
    ((BACKEND_TESTS_PASSED++))
else
    print_error "❌ Model tests failed"
    ((TOTAL_ERRORS++))
fi

print_status "Running Django Authentication Tests..."
if python -m pytest tests/test_auth.py -v --tb=short; then
    print_success "✅ Authentication tests passed"
    ((BACKEND_TESTS_PASSED++))
else
    print_error "❌ Authentication tests failed"
    ((TOTAL_ERRORS++))
fi

print_status "Running API Endpoint Tests..."
if python -m pytest tests/test_api_endpoints.py -v --tb=short; then
    print_success "✅ API endpoint tests passed"
    ((BACKEND_TESTS_PASSED++))
else
    print_error "❌ API endpoint tests failed"
    ((TOTAL_ERRORS++))
fi

print_status "Running Integration Tests..."
if python -m pytest tests/test_integration.py -v --tb=short; then
    print_success "✅ Integration tests passed"
    ((BACKEND_TESTS_PASSED++))
else
    print_error "❌ Integration tests failed"
    ((TOTAL_ERRORS++))
fi

# Run all backend tests with coverage
print_status "Running Full Backend Test Suite with Coverage..."
if python -m pytest tests/ --cov=user_auth --cov=backend --cov-report=html --cov-report=term-missing -v; then
    print_success "✅ Full backend test suite completed"
else
    print_error "❌ Some backend tests failed"
    ((TOTAL_ERRORS++))
fi

cd ..

# Frontend Tests
print_status "📋 Running Frontend Tests (React/Vitest)"
echo "----------------------------------------"

cd Frontend-ts

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    print_warning "Node modules not found. Installing dependencies..."
    npm install
fi

# Run React tests
print_status "Running Component Tests..."
if npm run test -- --run UserManagement.test.tsx; then
    print_success "✅ UserManagement component tests passed"
    ((FRONTEND_TESTS_PASSED++))
else
    print_error "❌ UserManagement component tests failed"
    ((TOTAL_ERRORS++))
fi

print_status "Running Authentication Tests..."
if npm run test -- --run Login.test.tsx Register.test.tsx AuthContext.test.tsx; then
    print_success "✅ Authentication component tests passed"
    ((FRONTEND_TESTS_PASSED++))
else
    print_error "❌ Authentication component tests failed"
    ((TOTAL_ERRORS++))
fi

print_status "Running Service Tests..."
if npm run test -- --run authService.test.ts; then
    print_success "✅ Service tests passed"
    ((FRONTEND_TESTS_PASSED++))
else
    print_error "❌ Service tests failed"
    ((TOTAL_ERRORS++))
fi

print_status "Running Private Route Tests..."
if npm run test -- --run PrivateRoute.test.tsx; then
    print_success "✅ Private route tests passed"
    ((FRONTEND_TESTS_PASSED++))
else
    print_error "❌ Private route tests failed"
    ((TOTAL_ERRORS++))
fi

print_status "Running End-to-End Tests..."
if npm run test -- --run App.e2e.test.tsx; then
    print_success "✅ End-to-end tests passed"
    ((FRONTEND_TESTS_PASSED++))
else
    print_error "❌ End-to-end tests failed"
    ((TOTAL_ERRORS++))
fi

# Run all frontend tests with coverage
print_status "Running Full Frontend Test Suite with Coverage..."
if npm run test:coverage; then
    print_success "✅ Full frontend test suite completed"
else
    print_error "❌ Some frontend tests failed"
    ((TOTAL_ERRORS++))
fi

cd ..

# Summary
echo ""
echo "=========================================================="
print_status "🏆 Test Results Summary"
echo "=========================================================="

echo "Backend Tests: $BACKEND_TESTS_PASSED test suites"
echo "Frontend Tests: $FRONTEND_TESTS_PASSED test suites"
echo "Total Errors: $TOTAL_ERRORS"

if [ $TOTAL_ERRORS -eq 0 ]; then
    print_success "🎉 All tests passed successfully!"
    echo ""
    print_success "✅ Your application is ready for further development!"
    echo ""
    echo "📊 Coverage Reports:"
    echo "  - Backend: backend/htmlcov/index.html"
    echo "  - Frontend: Frontend-ts/coverage/index.html"
else
    print_error "❌ Some tests failed. Please review the errors above."
    echo ""
    echo "🔧 Next Steps:"
    echo "  1. Review failed test output above"
    echo "  2. Fix the failing tests"
    echo "  3. Run this script again"
fi

echo ""
echo "📋 Additional Test Commands:"
echo "  Backend: cd backend && python -m pytest tests/ -v"
echo "  Frontend: cd Frontend-ts && npm run test"
echo "  Watch mode: cd Frontend-ts && npm run test -- --watch"

exit $TOTAL_ERRORS
