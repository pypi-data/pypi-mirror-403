"""Tests for corporate device detection."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from triagent.security.corporate_detect import (
    _get_dns_domain_unix,
    _get_dns_domain_windows,
    _get_kerberos_realm,
    _is_corporate_domain,
    detect_corporate_environment,
)


class TestCorporateDomainValidation:
    """Test domain validation logic."""

    def test_corporate_domain_accepted(self) -> None:
        """Corporate domains should be accepted."""
        assert _is_corporate_domain("us.deloitte.com") is True
        assert _is_corporate_domain("deloitte.com") is True
        assert _is_corporate_domain("corp.company.com") is True
        assert _is_corporate_domain("example.org") is True

    def test_non_corporate_domain_rejected(self) -> None:
        """Non-corporate domains should be rejected."""
        assert _is_corporate_domain("local") is False
        assert _is_corporate_domain("home") is False
        assert _is_corporate_domain("lan") is False
        assert _is_corporate_domain("localdomain") is False
        assert _is_corporate_domain("workgroup") is False
        assert _is_corporate_domain("mshome.net") is False
        assert _is_corporate_domain("internal") is False
        assert _is_corporate_domain("compute.internal") is False

    def test_nested_non_corporate_rejected(self) -> None:
        """Nested non-corporate domains should be rejected."""
        assert _is_corporate_domain("router.local") is False
        assert _is_corporate_domain("my.home") is False
        assert _is_corporate_domain("device.lan") is False
        assert _is_corporate_domain("aws.compute.internal") is False

    def test_single_word_rejected(self) -> None:
        """Single-word domains without dot should be rejected."""
        assert _is_corporate_domain("localhost") is False
        assert _is_corporate_domain("mycomputer") is False


class TestDNSDetectionUnix:
    """Test DNS detection on Unix/Mac."""

    def test_dns_domain_from_search(self, tmp_path) -> None:
        """Should extract domain from 'search' directive."""
        resolv_conf = tmp_path / "resolv.conf"
        resolv_conf.write_text("search us.deloitte.com deloitte.com\nnameserver 10.0.0.1\n")

        with patch(
            "triagent.security.corporate_detect.Path"
        ) as mock_path_class:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path.read_text.return_value = resolv_conf.read_text()
            mock_path_class.return_value = mock_path

            result = _get_dns_domain_unix()
            assert result == "us.deloitte.com"

    def test_dns_domain_from_domain_directive(self, tmp_path) -> None:
        """Should extract domain from 'domain' directive."""
        resolv_conf = tmp_path / "resolv.conf"
        resolv_conf.write_text("domain corp.example.com\nnameserver 10.0.0.1\n")

        with patch(
            "triagent.security.corporate_detect.Path"
        ) as mock_path_class:
            mock_path = MagicMock()
            mock_path.exists.return_value = True
            mock_path.read_text.return_value = resolv_conf.read_text()
            mock_path_class.return_value = mock_path

            result = _get_dns_domain_unix()
            assert result == "corp.example.com"

    def test_dns_domain_not_found(self) -> None:
        """Should return None if resolv.conf doesn't exist."""
        with patch(
            "triagent.security.corporate_detect.Path"
        ) as mock_path_class:
            mock_path = MagicMock()
            mock_path.exists.return_value = False
            mock_path_class.return_value = mock_path

            result = _get_dns_domain_unix()
            assert result is None


class TestDNSDetectionWindows:
    """Test DNS detection on Windows."""

    def test_dns_domain_from_env(self, monkeypatch) -> None:
        """Should get domain from USERDNSDOMAIN env var."""
        monkeypatch.setenv("USERDNSDOMAIN", "US.DELOITTE.COM")
        result = _get_dns_domain_windows()
        assert result == "US.DELOITTE.COM"

    def test_dns_domain_workgroup_rejected(self, monkeypatch) -> None:
        """Should reject WORKGROUP as domain."""
        monkeypatch.setenv("USERDNSDOMAIN", "WORKGROUP")
        result = _get_dns_domain_windows()
        assert result is None

    def test_dns_domain_not_set(self, monkeypatch) -> None:
        """Should return None if env var not set."""
        monkeypatch.delenv("USERDNSDOMAIN", raising=False)
        result = _get_dns_domain_windows()
        assert result is None


class TestKerberosDetection:
    """Test Kerberos realm detection."""

    def test_kerberos_realm_from_principal(self) -> None:
        """Should extract realm from principal."""
        mock_output = """Ticket cache: KCM:1000
Default principal: user@US.DELOITTE.COM

Valid starting       Expires              Service principal
01/01/2024 10:00:00  01/01/2024 20:00:00  krbtgt/US.DELOITTE.COM@US.DELOITTE.COM
"""
        with patch("triagent.security.corporate_detect.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=mock_output)
            result = _get_kerberos_realm()
            assert result == "US.DELOITTE.COM"

    def test_kerberos_realm_from_krbtgt(self) -> None:
        """Should extract realm from krbtgt ticket."""
        mock_output = """Ticket cache: FILE:/tmp/krb5cc_1000

Valid starting       Expires              Service principal
01/01/2024 10:00:00  01/01/2024 20:00:00  krbtgt/CORP.EXAMPLE.COM@CORP.EXAMPLE.COM
"""
        with patch("triagent.security.corporate_detect.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout=mock_output)
            result = _get_kerberos_realm()
            assert result == "CORP.EXAMPLE.COM"

    def test_kerberos_no_tickets(self) -> None:
        """Should return None if no tickets."""
        with patch("triagent.security.corporate_detect.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1, stdout="")
            result = _get_kerberos_realm()
            assert result is None

    def test_kerberos_command_not_found(self) -> None:
        """Should return None if klist not installed."""
        with patch("triagent.security.corporate_detect.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()
            result = _get_kerberos_realm()
            assert result is None


class TestCorporateEnvironmentDetection:
    """Test overall corporate environment detection."""

    def test_detect_dns_domain(self, monkeypatch) -> None:
        """Should detect corporate environment via DNS domain."""
        monkeypatch.setattr(
            "triagent.security.corporate_detect._get_dns_domain",
            lambda: "us.deloitte.com",
        )
        monkeypatch.setattr(
            "triagent.security.corporate_detect._get_kerberos_realm",
            lambda: None,
        )

        result = detect_corporate_environment()

        assert result is not None
        assert result.type == "DNS"
        assert result.identifier == "us.deloitte.com"

    def test_detect_kerberos_fallback(self, monkeypatch) -> None:
        """Should fall back to Kerberos if DNS not available."""
        monkeypatch.setattr(
            "triagent.security.corporate_detect._get_dns_domain",
            lambda: None,
        )
        monkeypatch.setattr(
            "triagent.security.corporate_detect._get_kerberos_realm",
            lambda: "US.DELOITTE.COM",
        )

        result = detect_corporate_environment()

        assert result is not None
        assert result.type == "Kerberos"
        assert result.identifier == "US.DELOITTE.COM"

    def test_detect_non_corporate_dns(self, monkeypatch) -> None:
        """Should reject non-corporate DNS domains."""
        monkeypatch.setattr(
            "triagent.security.corporate_detect._get_dns_domain",
            lambda: "local",
        )
        monkeypatch.setattr(
            "triagent.security.corporate_detect._get_kerberos_realm",
            lambda: None,
        )
        monkeypatch.setattr(
            "triagent.security.corporate_detect._get_azure_ad_tenant",
            lambda: None,
        )
        monkeypatch.setattr(
            "triagent.security.corporate_detect._get_mdm_server_domain",
            lambda: None,
        )

        result = detect_corporate_environment()
        assert result is None

    def test_detect_no_indicators(self, monkeypatch) -> None:
        """Should return None if no corporate indicators."""
        monkeypatch.setattr(
            "triagent.security.corporate_detect._get_dns_domain",
            lambda: None,
        )
        monkeypatch.setattr(
            "triagent.security.corporate_detect._get_kerberos_realm",
            lambda: None,
        )
        monkeypatch.setattr(
            "triagent.security.corporate_detect._get_azure_ad_tenant",
            lambda: None,
        )
        monkeypatch.setattr(
            "triagent.security.corporate_detect._get_mdm_server_domain",
            lambda: None,
        )

        result = detect_corporate_environment()
        assert result is None
