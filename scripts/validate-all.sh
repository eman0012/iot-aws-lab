#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}   IoT Platform Validation Script${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

ERRORS=0
WARNINGS=0

# Function to check command exists
check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 is installed"
        return 0
    else
        echo -e "${RED}✗${NC} $1 is not installed"
        ((ERRORS++))
        return 1
    fi
}

# Function to validate file exists
check_file() {
    if [ -f "$PROJECT_ROOT/$1" ]; then
        echo -e "${GREEN}✓${NC} $1 exists"
        return 0
    else
        echo -e "${RED}✗${NC} $1 is missing"
        ((ERRORS++))
        return 1
    fi
}

# Function to validate directory exists
check_dir() {
    if [ -d "$PROJECT_ROOT/$1" ]; then
        echo -e "${GREEN}✓${NC} $1/ exists"
        return 0
    else
        echo -e "${RED}✗${NC} $1/ is missing"
        ((ERRORS++))
        return 1
    fi
}

echo -e "${YELLOW}1. Checking Required Tools${NC}"
echo "-----------------------------------"
check_command terraform
check_command aws
check_command go
check_command python3
check_command docker
echo ""

echo -e "${YELLOW}2. Checking Project Structure${NC}"
echo "-----------------------------------"
check_dir "terraform"
check_dir "terraform/modules"
check_dir "lambda"
check_dir "go-cli"
check_dir "docker"
check_dir ".github/workflows"
check_dir "scripts"
echo ""

echo -e "${YELLOW}3. Checking Terraform Files${NC}"
echo "-----------------------------------"
check_file "terraform/versions.tf"
check_file "terraform/providers.tf"
check_file "terraform/variables.tf"
check_file "terraform/main.tf"
check_file "terraform/outputs.tf"
echo ""

echo -e "${YELLOW}4. Checking Terraform Modules${NC}"
echo "-----------------------------------"
MODULES=("vpc" "rds" "rabbitmq" "secrets" "s3" "lambda" "monitoring" "iot-core" "eventbridge" "ecs" "eks")
for module in "${MODULES[@]}"; do
    check_dir "terraform/modules/$module"
done
echo ""

echo -e "${YELLOW}5. Validating Terraform Syntax${NC}"
echo "-----------------------------------"
cd "$PROJECT_ROOT/terraform"
if terraform fmt -check -recursive > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Terraform formatting is correct"
else
    echo -e "${YELLOW}⚠${NC} Terraform needs formatting (running terraform fmt...)"
    terraform fmt -recursive
    ((WARNINGS++))
fi

if [ -d ".terraform" ]; then
    if terraform validate -json > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Terraform syntax is valid"
    else
        echo -e "${RED}✗${NC} Terraform validation failed"
        terraform validate
        ((ERRORS++))
    fi
else
    echo -e "${YELLOW}⚠${NC} Terraform not initialized (run 'terraform init' to validate)"
    ((WARNINGS++))
fi
cd "$PROJECT_ROOT"
echo ""

echo -e "${YELLOW}6. Checking Lambda Files${NC}"
echo "-----------------------------------"
# Shared files
check_file "lambda/shared/__init__.py"
check_file "lambda/shared/config.py"
check_file "lambda/shared/db_service.py"
check_file "lambda/shared/rabbitmq_service.py"
check_file "lambda/shared/auth.py"
check_file "lambda/shared/response.py"

# Handler files
HANDLERS=("users" "devices" "telemetry" "conditions" "alertlogs" "admin")
for handler in "${HANDLERS[@]}"; do
    check_file "lambda/$handler/handler.py"
done

check_file "lambda/build_all.sh"
check_file "lambda/requirements.txt"
echo ""

echo -e "${YELLOW}7. Validating Python Syntax${NC}"
echo "-----------------------------------"
PYTHON_ERRORS=0
for pyfile in "$PROJECT_ROOT"/lambda/shared/*.py "$PROJECT_ROOT"/lambda/*/handler.py; do
    if [ -f "$pyfile" ]; then
        if python3 -m py_compile "$pyfile" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} $(basename $pyfile) syntax valid"
        else
            echo -e "${RED}✗${NC} $(basename $pyfile) has syntax errors"
            python3 -m py_compile "$pyfile"
            ((PYTHON_ERRORS++))
        fi
    fi
done

if [ $PYTHON_ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓${NC} All Python files have valid syntax"
else
    ((ERRORS+=$PYTHON_ERRORS))
fi
echo ""

echo -e "${YELLOW}8. Checking Go CLI Files${NC}"
echo "-----------------------------------"
check_file "go-cli/go.mod"
check_file "go-cli/cmd/main.go"
check_file "go-cli/README.md"
echo ""

echo -e "${YELLOW}9. Validating Go Code${NC}"
echo "-----------------------------------"
cd "$PROJECT_ROOT/go-cli"
if go fmt ./... > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Go code is formatted"
else
    echo -e "${YELLOW}⚠${NC} Go code formatting issues"
    ((WARNINGS++))
fi

if go vet ./... 2>&1 | grep -q "no Go files"; then
    echo -e "${GREEN}✓${NC} Go code structure is valid"
elif go vet ./... > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Go vet passed"
else
    echo -e "${RED}✗${NC} Go vet found issues"
    go vet ./...
    ((ERRORS++))
fi

if go build -o /tmp/iot-cli-test ./cmd/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Go build successful"
    rm -f /tmp/iot-cli-test
else
    echo -e "${RED}✗${NC} Go build failed"
    go build -o /tmp/iot-cli-test ./cmd/
    ((ERRORS++))
fi
cd "$PROJECT_ROOT"
echo ""

echo -e "${YELLOW}10. Checking Docker Files${NC}"
echo "-----------------------------------"
check_file "docker/go-cli/Dockerfile"
check_file "docker-compose.yml"
echo ""

echo -e "${YELLOW}11. Checking CI/CD Workflows${NC}"
echo "-----------------------------------"
check_file ".github/workflows/terraform.yml"
check_file ".github/workflows/lambda-deploy.yml"
check_file ".github/workflows/go-build.yml"
echo ""

echo -e "${YELLOW}12. Checking Documentation${NC}"
echo "-----------------------------------"
check_file "README.md"
check_file "MIGRATION_PROGRESS.md"
check_file ".gitignore"
echo ""

echo -e "${YELLOW}13. Checking Lambda Build Script${NC}"
echo "-----------------------------------"
if [ -x "$PROJECT_ROOT/lambda/build_all.sh" ]; then
    echo -e "${GREEN}✓${NC} lambda/build_all.sh is executable"
else
    echo -e "${YELLOW}⚠${NC} lambda/build_all.sh is not executable (fixing...)"
    chmod +x "$PROJECT_ROOT/lambda/build_all.sh"
    ((WARNINGS++))
fi
echo ""

echo -e "${YELLOW}14. Checking File Counts${NC}"
echo "-----------------------------------"
TERRAFORM_FILES=$(find "$PROJECT_ROOT/terraform" -name "*.tf" | wc -l)
PYTHON_FILES=$(find "$PROJECT_ROOT/lambda" -name "*.py" | wc -l)
GO_FILES=$(find "$PROJECT_ROOT/go-cli" -name "*.go" | wc -l)

echo -e "${BLUE}Terraform files:${NC} $TERRAFORM_FILES"
echo -e "${BLUE}Python files:${NC} $PYTHON_FILES"
echo -e "${BLUE}Go files:${NC} $GO_FILES"
echo ""

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}   Validation Summary${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✓ All validations passed!${NC}"
    echo -e "${GREEN}✓ Project is ready for deployment${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠ Validation completed with $WARNINGS warning(s)${NC}"
    echo -e "${GREEN}✓ No critical errors found${NC}"
    exit 0
else
    echo -e "${RED}✗ Validation failed with $ERRORS error(s) and $WARNINGS warning(s)${NC}"
    echo -e "${RED}✗ Please fix the errors above before deployment${NC}"
    exit 1
fi
