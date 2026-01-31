"""Tests for CLI module."""

import argparse
from cgc_common.cli import ServerArgs, add_server_args, resolve_host


class TestServerArgs:
    def test_from_namespace(self):
        ns = argparse.Namespace(host="0.0.0.0", port=8080, share=True)
        args = ServerArgs.from_namespace(ns)
        assert args.host == "0.0.0.0"
        assert args.port == 8080
        assert args.share is True

    def test_from_namespace_defaults(self):
        ns = argparse.Namespace()
        args = ServerArgs.from_namespace(ns)
        assert args.host == "127.0.0.1"
        assert args.port == 7865
        assert args.share is False


class TestAddServerArgs:
    def test_default_values(self):
        parser = argparse.ArgumentParser()
        add_server_args(parser)
        args = parser.parse_args([])
        assert args.host == "127.0.0.1"
        assert args.port == 7865
        assert args.share is False

    def test_custom_defaults(self):
        parser = argparse.ArgumentParser()
        add_server_args(parser, default_port=9000, default_host="0.0.0.0")
        args = parser.parse_args([])
        assert args.host == "0.0.0.0"
        assert args.port == 9000

    def test_cli_overrides(self):
        parser = argparse.ArgumentParser()
        add_server_args(parser)
        args = parser.parse_args(["--host", "192.168.1.1", "--port", "8000", "--share"])
        assert args.host == "192.168.1.1"
        assert args.port == 8000
        assert args.share is True


class TestResolveHost:
    def test_explicit_argument(self):
        args = argparse.Namespace(host="explicit.host")
        assert resolve_host(args) == "explicit.host"

    def test_default_fallback(self):
        args = argparse.Namespace(host=None)
        assert resolve_host(args) == "127.0.0.1"

    def test_custom_default(self):
        args = argparse.Namespace(host=None)
        assert resolve_host(args, default="0.0.0.0") == "0.0.0.0"

    def test_config_class_with_security_mixin(self):
        class MockConfig:
            @classmethod
            def get_server_bind(cls):
                return "from_config"

        args = argparse.Namespace(host=None)
        assert resolve_host(args, config_class=MockConfig) == "from_config"

    def test_explicit_overrides_config(self):
        class MockConfig:
            @classmethod
            def get_server_bind(cls):
                return "from_config"

        args = argparse.Namespace(host="explicit")
        assert resolve_host(args, config_class=MockConfig) == "explicit"
