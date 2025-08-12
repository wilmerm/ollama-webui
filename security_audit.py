#!/usr/bin/env python3
"""
Security validation script for Ollama WebUI

This script validates security configurations and best practices.
"""

import os
import re
import sys
from pathlib import Path

def check_env_file():
    """Check if .env file follows security best practices"""
    env_path = Path(".env")
    env_example_path = Path(".env.example")
    
    issues = []
    
    # Check if .env.example exists
    if not env_example_path.exists():
        issues.append("❌ .env.example file not found")
    else:
        print("✅ .env.example file exists")
    
    # If .env exists, check for insecure values
    if env_path.exists():
        with open(env_path, 'r') as f:
            content = f.read()
            
        if 'ALLOWED_HOSTS=*' in content:
            issues.append("❌ ALLOWED_HOSTS=* is insecure for production")
        
        if 'CORS_ORIGINS=*' in content or 'allow_origins=["*"]' in content:
            issues.append("❌ CORS wildcard (*) is insecure for production")
            
        if 'DEBUG=True' in content:
            issues.append("⚠️  DEBUG=True should be False in production")
    
    return issues

def check_source_code():
    """Check source code for potential security issues"""
    issues = []
    
    # Check backend main.py
    backend_path = Path("backend/main.py")
    if backend_path.exists():
        with open(backend_path, 'r') as f:
            content = f.read()
            
        # Check for wildcard CORS
        if 'allow_origins=["*"]' in content:
            issues.append("❌ Backend uses wildcard CORS origins")
        
        # Check for proper error handling
        if 'detail=str(e)' in content:
            issues.append("❌ Backend exposes detailed error messages")
        
        # Check if security headers are present
        if 'X-Content-Type-Options' not in content:
            issues.append("❌ Missing security headers")
    
    # Check for hard-coded secrets
    for ext in ['*.py', '*.js', '*.vue']:
        for file_path in Path('.').rglob(ext):
            if '.git' in str(file_path) or 'node_modules' in str(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                # Check for potential API keys or tokens
                secret_patterns = [
                    r'(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*["\'][^"\']{20,}["\']',
                    r'(?i)(sk-[a-zA-Z0-9]{20,})',  # OpenAI-style keys
                    r'(?i)(ghp_[a-zA-Z0-9]{36})',  # GitHub tokens
                ]
                
                for pattern in secret_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        issues.append(f"⚠️  Potential secret in {file_path}: {matches[0][:10]}...")
                        
            except Exception:
                continue
    
    return issues

def check_gitignore():
    """Check if .gitignore properly excludes sensitive files"""
    issues = []
    gitignore_path = Path(".gitignore")
    
    if not gitignore_path.exists():
        issues.append("❌ .gitignore file not found")
        return issues
    
    with open(gitignore_path, 'r') as f:
        content = f.read()
    
    required_patterns = ['.env', '*.log', '__pycache__/', 'node_modules/']
    
    for pattern in required_patterns:
        if pattern not in content:
            issues.append(f"⚠️  .gitignore missing pattern: {pattern}")
    
    print("✅ .gitignore exists and excludes sensitive files")
    return issues

def check_dependencies():
    """Check for security-relevant dependency configurations"""
    issues = []
    
    # Check if security documentation exists
    security_files = ['SECURITY.md', 'security.md']
    if not any(Path(f).exists() for f in security_files):
        issues.append("⚠️  No security documentation found")
    else:
        print("✅ Security documentation exists")
    
    return issues

def main():
    """Run all security checks"""
    print("🔒 Running Ollama WebUI Security Audit")
    print("=" * 40)
    
    all_issues = []
    
    print("\n📋 Checking environment configuration...")
    all_issues.extend(check_env_file())
    
    print("\n📋 Checking source code...")
    all_issues.extend(check_source_code())
    
    print("\n📋 Checking .gitignore...")
    all_issues.extend(check_gitignore())
    
    print("\n📋 Checking documentation...")
    all_issues.extend(check_dependencies())
    
    print("\n" + "=" * 40)
    print("📊 Security Audit Results")
    print("=" * 40)
    
    if not all_issues:
        print("✅ No security issues found!")
        return 0
    
    print(f"Found {len(all_issues)} security issues:")
    for issue in all_issues:
        print(f"  {issue}")
    
    print("\n💡 Recommendations:")
    print("  1. Review the SECURITY.md file for best practices")
    print("  2. Use .env.example as a template for secure configuration")
    print("  3. Never commit .env files to version control")
    print("  4. Use specific hostnames instead of wildcards in production")
    
    return len(all_issues)

if __name__ == "__main__":
    sys.exit(main())