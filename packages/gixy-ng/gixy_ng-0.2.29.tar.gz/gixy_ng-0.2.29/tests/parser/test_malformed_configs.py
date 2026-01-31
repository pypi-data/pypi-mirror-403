"""Tests for graceful handling of malformed nginx configurations."""

import pytest

from gixy.core.exceptions import InvalidConfiguration
from gixy.directives.block import LocationBlock, MapBlock, IfBlock
from gixy.directives.directive import (
    AddHeaderDirective,
    SetDirective,
    RewriteDirective,
)
from gixy.parser.nginx_parser import NginxParser


def _parse(config):
    return NginxParser(cwd="", allow_includes=False).parse_string(config)


class TestMalformedDirectives:
    """Test that malformed directives raise InvalidConfiguration."""

    def test_add_header_missing_value(self):
        """add_header requires 2-3 args."""
        with pytest.raises(
            InvalidConfiguration, match='Failed to parse "add_header" directive'
        ):
            _parse("add_header X-Test;")

    def test_add_header_no_args(self):
        """add_header with no args should fail."""
        with pytest.raises(
            InvalidConfiguration, match='Failed to parse "add_header" directive'
        ):
            _parse("add_header;")

    def test_set_missing_value(self):
        """set requires exactly 2 args."""
        with pytest.raises(
            InvalidConfiguration, match='Failed to parse "set" directive'
        ):
            _parse("set $foo;")

    def test_set_no_args(self):
        """set with no args should fail."""
        with pytest.raises(
            InvalidConfiguration, match='Failed to parse "set" directive'
        ):
            _parse("set;")

    def test_auth_request_set_missing_value(self):
        """auth_request_set requires exactly 2 args."""
        with pytest.raises(
            InvalidConfiguration, match='Failed to parse "auth_request_set" directive'
        ):
            _parse("auth_request_set $foo;")

    def test_perl_set_missing_value(self):
        """perl_set requires exactly 2 args."""
        with pytest.raises(
            InvalidConfiguration, match='Failed to parse "perl_set" directive'
        ):
            _parse("perl_set $foo;")

    def test_set_by_lua_missing_value(self):
        """set_by_lua requires 2+ args."""
        with pytest.raises(
            InvalidConfiguration, match='Failed to parse "set_by_lua" directive'
        ):
            _parse("set_by_lua $foo;")

    def test_rewrite_missing_replacement(self):
        """rewrite requires 2-3 args."""
        with pytest.raises(
            InvalidConfiguration, match='Failed to parse "rewrite" directive'
        ):
            _parse("rewrite ^/old;")

    def test_rewrite_no_args(self):
        """rewrite with no args should fail."""
        with pytest.raises(
            InvalidConfiguration, match='Failed to parse "rewrite" directive'
        ):
            _parse("rewrite;")


class TestMalformedBlocks:
    """Test that malformed blocks raise InvalidConfiguration."""

    def test_location_no_args(self):
        """location requires 1-2 args."""
        with pytest.raises(
            InvalidConfiguration, match='Failed to parse "location" directive'
        ):
            _parse("location {}")

    def test_map_missing_destination(self):
        """map requires exactly 2 args - Jim's original bug case."""
        with pytest.raises(
            InvalidConfiguration, match='Failed to parse "map" directive'
        ):
            _parse("map $uri {}")

    def test_map_no_args(self):
        """map with no args should fail."""
        with pytest.raises(
            InvalidConfiguration, match='Failed to parse "map" directive'
        ):
            _parse("map {}")

    def test_include_no_args(self):
        """include requires exactly 1 arg."""
        with pytest.raises(
            InvalidConfiguration, match='Failed to parse "include" directive'
        ):
            _parse("include;")

    def test_if_invalid_args(self):
        """if with 4+ args should fail."""
        with pytest.raises(InvalidConfiguration, match='Unknown "if" definition'):
            _parse("if ($a = b c d) {}")


class TestValidEdgeCases:
    """Test that valid edge cases still work correctly."""

    def test_location_with_modifier(self):
        """location ~ /regex should work."""
        tree = _parse("location ~ ^/api { }")
        location = tree.children[0]
        assert isinstance(location, LocationBlock)
        assert location.modifier == "~"
        assert location.path == "^/api"

    def test_location_without_modifier(self):
        """location /path should work."""
        tree = _parse("location /api { }")
        location = tree.children[0]
        assert isinstance(location, LocationBlock)
        assert location.modifier is None
        assert location.path == "/api"

    def test_location_exact_match(self):
        """location = /exact should work."""
        tree = _parse("location = /exact { }")
        location = tree.children[0]
        assert isinstance(location, LocationBlock)
        assert location.modifier == "="
        assert location.path == "/exact"

    def test_rewrite_with_flag(self):
        """rewrite with flag should work."""
        tree = _parse("rewrite ^/old /new permanent;")
        rewrite = tree.children[0]
        assert isinstance(rewrite, RewriteDirective)
        assert rewrite.pattern == "^/old"
        assert rewrite.replace == "/new"
        assert rewrite.flag == "permanent"

    def test_rewrite_without_flag(self):
        """rewrite without flag should work."""
        tree = _parse("rewrite ^/old /new;")
        rewrite = tree.children[0]
        assert isinstance(rewrite, RewriteDirective)
        assert rewrite.pattern == "^/old"
        assert rewrite.replace == "/new"
        assert rewrite.flag is None

    def test_add_header_with_always(self):
        """add_header with always flag should work."""
        tree = _parse("add_header X-Test value always;")
        add_header = tree.children[0]
        assert isinstance(add_header, AddHeaderDirective)
        assert add_header.header == "x-test"
        assert add_header.value == "value"
        assert add_header.always is True

    def test_add_header_without_always(self):
        """add_header without always flag should work."""
        tree = _parse("add_header X-Test value;")
        add_header = tree.children[0]
        assert isinstance(add_header, AddHeaderDirective)
        assert add_header.header == "x-test"
        assert add_header.value == "value"
        assert add_header.always is False

    def test_set_directive(self):
        """set with 2 args should work."""
        tree = _parse("set $foo bar;")
        set_dir = tree.children[0]
        assert isinstance(set_dir, SetDirective)
        assert set_dir.variable == "foo"
        assert set_dir.value == "bar"

    def test_map_block(self):
        """map with 2 args should work."""
        tree = _parse("map $uri $mapped { default 0; }")
        map_block = tree.children[0]
        assert isinstance(map_block, MapBlock)
        assert map_block.source == "$uri"
        assert map_block.variable == "mapped"

    def test_map_empty_source_valid(self):
        """Jim's valid pattern: map "" $myvar should work."""
        tree = _parse('map "" $myvar { default ""; }')
        map_block = tree.children[0]
        assert isinstance(map_block, MapBlock)
        assert map_block.source == ""
        assert map_block.variable == "myvar"

    def test_if_single_variable(self):
        """if ($var) should work."""
        tree = _parse("if ($slow) { }")
        if_block = tree.children[0]
        assert isinstance(if_block, IfBlock)
        assert if_block.variable == "$slow"

    def test_if_file_check(self):
        """if (-f $file) should work."""
        tree = _parse("if (-f $request_filename) { }")
        if_block = tree.children[0]
        assert isinstance(if_block, IfBlock)
        assert if_block.operand == "-f"
        assert if_block.value == "$request_filename"

    def test_if_comparison(self):
        """if ($var = value) should work."""
        tree = _parse("if ($request_method = POST) { }")
        if_block = tree.children[0]
        assert isinstance(if_block, IfBlock)
        assert if_block.variable == "$request_method"
        assert if_block.operand == "="
        assert if_block.value == "POST"

    def test_if_regex(self):
        """if ($var ~ regex) should work."""
        tree = _parse("if ($request_uri ~ ^/admin) { }")
        if_block = tree.children[0]
        assert isinstance(if_block, IfBlock)
        assert if_block.variable == "$request_uri"
        assert if_block.operand == "~"
        assert if_block.value == "^/admin"
