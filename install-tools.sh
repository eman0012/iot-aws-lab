#!/bin/bash
set -e

echo "======================================"
echo "Installing AWS Migration Tools"
echo "======================================"
echo ""

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew is not installed. Please install it first:"
    echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    exit 1
fi

echo "✅ Homebrew is installed"
echo ""

# Update Homebrew
echo "📦 Updating Homebrew..."
brew update

# Install AWS CLI
echo ""
echo "📦 Installing AWS CLI..."
if command -v aws &> /dev/null; then
    echo "✅ AWS CLI already installed ($(aws --version))"
else
    brew install awscli
    echo "✅ AWS CLI installed"
fi

# Install Terraform
echo ""
echo "📦 Installing Terraform..."
if command -v terraform &> /dev/null; then
    echo "✅ Terraform already installed ($(terraform --version | head -n1))"
else
    brew tap hashicorp/tap
    brew install hashicorp/tap/terraform
    echo "✅ Terraform installed"
fi

# Install Go
echo ""
echo "📦 Installing Go..."
if command -v go &> /dev/null; then
    echo "✅ Go already installed ($(go version))"
else
    brew install go
    echo "✅ Go installed"
fi

# Install PostgreSQL client
echo ""
echo "📦 Installing PostgreSQL client..."
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL client already installed ($(psql --version))"
else
    brew install libpq
    # Add to PATH (Homebrew doesn't link libpq by default to avoid conflicts)
    echo 'export PATH="/opt/homebrew/opt/libpq/bin:$PATH"' >> ~/.zshrc
    export PATH="/opt/homebrew/opt/libpq/bin:$PATH"
    echo "✅ PostgreSQL client installed"
    echo "⚠️  Note: You may need to restart your terminal or run: source ~/.zshrc"
fi

echo ""
echo "======================================"
echo "Installation Complete!"
echo "======================================"
echo ""
echo "Installed versions:"
aws --version 2>/dev/null || echo "  AWS CLI: not in PATH yet"
terraform --version 2>/dev/null | head -n1 || echo "  Terraform: not in PATH yet"
go version 2>/dev/null || echo "  Go: not in PATH yet"
docker --version 2>/dev/null || echo "  Docker: $(docker --version)"
node --version 2>/dev/null | sed 's/^/  Node.js: /' || echo "  Node.js: not found"
npm --version 2>/dev/null | sed 's/^/  npm: /' || echo "  npm: not found"
psql --version 2>/dev/null || echo "  PostgreSQL: not in PATH yet"
jq --version 2>/dev/null | sed 's/^/  jq: /' || echo "  jq: not found"

echo ""
echo "======================================"
echo "Next Steps:"
echo "======================================"
echo ""
echo "1. Configure AWS CLI:"
echo "   aws configure"
echo ""
echo "   You'll need:"
echo "   - AWS Access Key ID"
echo "   - AWS Secret Access Key"
echo "   - Default region: ca-central-1"
echo "   - Default output format: json"
echo ""
echo "2. Verify AWS authentication:"
echo "   aws sts get-caller-identity"
echo ""
echo "3. If tools aren't in PATH, restart your terminal or run:"
echo "   source ~/.zshrc"
echo ""
