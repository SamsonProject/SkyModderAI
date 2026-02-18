"""
Tests for OpenCLAW modules.
"""

import os
import shutil
import tempfile
import pytest
from pathlib import Path

from openclaw_engine import (
    build_openclaw_plan,
    validate_plan_safety,
    validate_permissions,
    PermissionScope,
)
from dev.openclaw.sandbox import (
    OpenClawSandbox,
    SandboxError,
    SandboxPathError,
    SandboxPermissionError,
    SandboxSizeError,
)
from dev.openclaw.guard import (
    GuardChecker,
    guard_check,
    GuardCheckResult,
)
from dev.openclaw.automator import (
    OpenClawAutomator,
    execute_plan,
    PlanExecutionResult,
)


# =============================================================================
# OpenCLAW Engine Tests
# =============================================================================


class TestPermissionScope:
    """Tests for PermissionScope enum."""
    
    def test_permission_scopes_defined(self):
        """Test that all expected permission scopes are defined."""
        expected_scopes = {
            "launch_game",
            "read_game_logs",
            "read_performance_metrics",
            "controller_signal",
            "input_signal_aggregate",
            "internet_research",
            "write_sandbox_files",
            "suggest_mod_tweaks",
        }
        actual_scopes = set(PermissionScope)
        assert expected_scopes == actual_scopes


class TestBuildOpenClawPlan:
    """Tests for build_openclaw_plan function."""
    
    def test_build_plan_minimal(self):
        """Test building a plan with minimal permissions."""
        plan = build_openclaw_plan(
            game="skyrimse",
            objective="test",
            playstyle="balanced",
            permissions={},
        )
        
        assert plan["game"] == "skyrimse"
        assert plan["objective"] == "test"
        assert plan["playstyle"] == "balanced"
        assert "actions" in plan
        assert "safety_contract" in plan
        
        # Safety contract should be strict
        safety = plan["safety_contract"]
        assert safety["requires_manual_confirmation"] is True
        assert safety["no_system_level_operations"] is True
        assert safety["sandbox_first"] is True
        assert safety["rollback_before_apply"] is True
    
    def test_build_plan_with_permissions(self):
        """Test building a plan with various permissions."""
        permissions = {
            PermissionScope.LAUNCH_GAME: True,
            PermissionScope.READ_GAME_LOGS: True,
            PermissionScope.WRITE_SANDBOX_FILES: True,
        }
        
        plan = build_openclaw_plan(
            game="fallout4",
            objective="improve FPS",
            playstyle="performance",
            permissions=permissions,
        )
        
        # Should have more actions with permissions
        action_kinds = [a["kind"] for a in plan["actions"]]
        assert "analyze_current_state" in action_kinds
        assert "read_runtime_logs" in action_kinds
        assert "sandbox_write" in action_kinds
        assert "launch_intent" in action_kinds
    
    def test_build_plan_defaults(self):
        """Test that plan uses defaults for missing parameters."""
        plan = build_openclaw_plan(
            game="",
            objective="",
            playstyle="",
            permissions={},
        )
        
        assert plan["game"] == "skyrimse"  # Default
        assert "stability" in plan["objective"]  # Default
        assert plan["playstyle"] == "balanced"  # Default


class TestValidatePlanSafety:
    """Tests for validate_plan_safety function."""
    
    def test_validate_safe_plan(self):
        """Test validating a safe plan."""
        plan = build_openclaw_plan(
            game="skyrimse",
            objective="test",
            playstyle="balanced",
            permissions={},
        )
        
        is_safe, violations = validate_plan_safety(plan)
        assert is_safe is True
        assert len(violations) == 0
    
    def test_validate_unsafe_plan(self):
        """Test validating an unsafe plan."""
        plan = {
            "game": "skyrimse",
            "actions": [
                {
                    "kind": "modify_registry",  # Denied operation
                    "description": "Bad action",
                }
            ],
            "safety_contract": {
                "requires_manual_confirmation": False,  # Unsafe
            },
        }
        
        is_safe, violations = validate_plan_safety(plan)
        assert is_safe is False
        assert len(violations) > 0
        assert any("manual confirmation" in v for v in violations)
        assert any("modify_registry" in v for v in violations)


class TestValidatePermissions:
    """Tests for validate_permissions function."""
    
    def test_validate_valid_permissions(self):
        """Test validating valid permissions."""
        permissions = {
            PermissionScope.LAUNCH_GAME: True,
            PermissionScope.READ_GAME_LOGS: False,
        }
        
        is_valid, issues = validate_permissions(permissions)
        assert is_valid is True
    
    def test_validate_invalid_scope(self):
        """Test validating invalid permission scope."""
        permissions = {
            "invalid_scope": True,
        }
        
        is_valid, issues = validate_permissions(permissions)
        assert is_valid is False
        assert any("Unknown permission" in i for i in issues)


# =============================================================================
# OpenCLAW Sandbox Tests
# =============================================================================


class TestOpenClawSandbox:
    """Tests for OpenClawSandbox class."""
    
    @pytest.fixture
    def sandbox(self):
        """Create a temporary sandbox for testing."""
        temp_dir = tempfile.mkdtemp()
        sb = OpenClawSandbox(temp_dir, "test@example.com")
        yield sb
        shutil.rmtree(temp_dir)
    
    def test_sandbox_creation(self, sandbox):
        """Test sandbox is created correctly."""
        assert sandbox.sandbox_path.exists()
        assert sandbox.sandbox_path.is_dir()
    
    def test_sandbox_write_read(self, sandbox):
        """Test writing and reading files."""
        content = b"Hello, OpenCLAW!"
        rel_path = "test/file.txt"
        
        success, error = sandbox.safe_write(rel_path, content)
        assert success is True
        assert error is None
        
        read_content, error = sandbox.safe_read(rel_path)
        assert read_content == content
        assert error is None
    
    def test_sandbox_path_traversal_blocked(self, sandbox):
        """Test that path traversal is blocked."""
        # Try to escape sandbox
        success, error = sandbox.safe_write("../escape.txt", b"bad")
        assert success is False
        assert "traversal" in error.lower()
        
        success, error = sandbox.safe_write("subdir/../../escape.txt", b"bad")
        assert success is False
    
    def test_sandbox_denied_extension(self, sandbox):
        """Test that denied extensions are blocked."""
        success, error = sandbox.safe_write("test.exe", b"bad")
        assert success is False
        assert "extension" in error.lower()
    
    def test_sandbox_allowed_extensions(self, sandbox):
        """Test that allowed extensions work."""
        allowed = [
            "test.txt",
            "test.md",
            "test.json",
            "test.yaml",
            "test.esp",
            "test.log",
        ]
        
        for filename in allowed:
            success, error = sandbox.safe_write(filename, b"test")
            assert success is True, f"Failed for {filename}: {error}"
    
    def test_sandbox_delete(self, sandbox):
        """Test file deletion."""
        # Create file
        sandbox.safe_write("to_delete.txt", b"delete me")
        
        # Delete it
        success, error = sandbox.safe_delete("to_delete.txt")
        assert success is True
        
        # Verify deleted
        read_content, _ = sandbox.safe_read("to_delete.txt")
        assert read_content is None
    
    def test_sandbox_list(self, sandbox):
        """Test directory listing."""
        # Create some files
        sandbox.safe_write("file1.txt", b"1")
        sandbox.safe_write("file2.txt", b"2")
        sandbox.safe_write("subdir/file3.txt", b"3")
        
        files, error = sandbox.safe_list()
        assert error is None
        assert len(files) == 3
    
    def test_sandbox_size_limit(self, sandbox):
        """Test size limits."""
        # Try to write a huge file
        huge_content = b"x" * (100 * 1024 * 1024)  # 100MB
        success, error = sandbox.safe_write("huge.txt", huge_content)
        assert success is False
        assert "large" in error.lower()
    
    def test_sandbox_info(self, sandbox):
        """Test getting sandbox info."""
        info = sandbox.get_sandbox_info()
        
        assert "file_count" in info
        assert "total_bytes" in info
        assert "max_files" in info
        assert "max_bytes" in info


# =============================================================================
# OpenCLAW Guard Tests
# =============================================================================


class TestGuardChecker:
    """Tests for GuardChecker class."""
    
    @pytest.fixture
    def db(self):
        """Create a temporary database for testing."""
        import sqlite3
        temp_db = tempfile.mktemp(suffix=".db")
        conn = sqlite3.connect(temp_db)
        
        # Create permissions table
        conn.execute("""
            CREATE TABLE openclaw_permissions (
                user_email TEXT NOT NULL,
                scope TEXT NOT NULL,
                granted INTEGER DEFAULT 0,
                granted_at TIMESTAMP,
                PRIMARY KEY (user_email, scope)
            )
        """)
        conn.commit()
        
        yield conn
        
        conn.close()
        os.unlink(temp_db)
    
    def test_check_permission_granted(self, db):
        """Test checking granted permission."""
        # Grant permission
        db.execute(
            "INSERT INTO openclaw_permissions (user_email, scope, granted) VALUES (?, ?, 1)",
            ("test@example.com", "write_sandbox_files"),
        )
        db.commit()
        
        checker = GuardChecker(db)
        result = checker.check_permission_grant("test@example.com", "write")
        
        assert result.allowed is True
    
    def test_check_permission_not_granted(self, db):
        """Test checking non-granted permission."""
        checker = GuardChecker(db)
        result = checker.check_permission_grant("test@example.com", "write")
        
        assert result.allowed is False
        assert "not granted" in result.reasons[0].lower()
    
    def test_check_denied_operation(self, db):
        """Test checking denied operation."""
        checker = GuardChecker(db)
        result = checker.check_permission_grant("test@example.com", "modify_registry")
        
        assert result.allowed is False
        assert "not allowed" in result.reasons[0].lower()
    
    def test_check_path_safety_safe(self, db):
        """Test path safety check for safe path."""
        checker = GuardChecker(db)
        result = checker.check_path_safety("safe/path/file.txt", "write")
        
        assert result.allowed is True
    
    def test_check_path_safety_unsafe(self, db):
        """Test path safety check for unsafe path."""
        checker = GuardChecker(db)
        result = checker.check_path_safety("../escape.txt", "write")
        
        assert result.allowed is False
        assert "traversal" in result.reasons[0].lower()
    
    def test_guard_check_convenience(self, db):
        """Test the guard_check convenience function."""
        # Grant permission
        db.execute(
            "INSERT INTO openclaw_permissions (user_email, scope, granted) VALUES (?, ?, 1)",
            ("test@example.com", "write_sandbox_files"),
        )
        db.commit()
        
        result = guard_check(
            db,
            "test@example.com",
            "write",
            "safe/file.txt",
            1024,
        )
        
        assert result.allowed is True


# =============================================================================
# OpenCLAW Automator Tests
# =============================================================================


class TestOpenClawAutomator:
    """Tests for OpenClawAutomator class."""
    
    @pytest.fixture
    def automator(self):
        """Create an automator for testing."""
        import sqlite3
        temp_db = tempfile.mktemp(suffix=".db")
        temp_workspace = tempfile.mkdtemp()
        
        db = sqlite3.connect(temp_db)
        db.execute("""
            CREATE TABLE openclaw_permissions (
                user_email TEXT NOT NULL,
                scope TEXT NOT NULL,
                granted INTEGER DEFAULT 0,
                PRIMARY KEY (user_email, scope)
            )
        """)
        
        # Grant all permissions for testing
        for scope in PermissionScope:
            db.execute(
                "INSERT INTO openclaw_permissions VALUES (?, ?, 1, CURRENT_TIMESTAMP)",
                ("test@example.com", scope),
            )
        db.commit()
        
        automator = OpenClawAutomator(db, temp_workspace, "test@example.com")
        yield automator
        
        db.close()
        shutil.rmtree(temp_workspace)
        os.unlink(temp_db)
    
    def test_execute_plan_success(self, automator):
        """Test successful plan execution."""
        plan = build_openclaw_plan(
            game="skyrimse",
            objective="test",
            playstyle="balanced",
            permissions={PermissionScope.WRITE_SANDBOX_FILES: True},
        )
        
        result = automator.execute_plan(plan)
        
        assert result.success is True
        assert result.actions_executed > 0
        assert result.actions_failed == 0
    
    def test_execute_plan_result_to_dict(self, automator):
        """Test converting result to dictionary."""
        plan = build_openclaw_plan(
            game="skyrimse",
            objective="test",
            playstyle="balanced",
            permissions={},
        )
        
        result = automator.execute_plan(plan)
        result_dict = result.to_dict()
        
        assert "success" in result_dict
        assert "actions_executed" in result_dict
        assert "duration_seconds" in result_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
