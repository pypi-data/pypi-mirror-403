from gixy.parser.raw_parser import RawParser


def test_directive_simple():
    config = """
user http;
    """
    nodes = RawParser().parse(config)
    assert len(nodes) == 1
    n = nodes[0]
    assert n.get("kind") == "directive"
    assert n.get("name") == "user"
    assert n.get("args") == ["http"]


def test_if_args_flatten():
    config = """
if ($request_method = POST) {
}
    """
    nodes = RawParser().parse(config)
    # find the if-block
    if_nodes = [n for n in nodes if n.get("kind") == "block" and n.get("name") == "if"]
    assert len(if_nodes) == 1
    ifn = if_nodes[0]
    assert ifn.get("args") == ["$request_method", "=", "POST"]


def test_lua_block_raw_content():
    config = """
location = /lua {
 # MIME type determined by default_type:
 default_type 'text/plain';

 content_by_lua_block {
     local res = ngx.location.capture("/some_other_location")
     if res then
         ngx.say("status: ", res.status)
         ngx.say("body:")
         ngx.print(res.body)
     end
 }
}
    """
    nodes = RawParser().parse(config)

    def find_by_name(ns, name):
        for x in ns:
            if x.get("name") == name:
                yield x
            if x.get("kind") == "block":
                yield from find_by_name(x.get("children", []), name)

    lua_blocks = [
        b
        for b in find_by_name(nodes, "content_by_lua_block")
        if b.get("kind") == "block"
    ]
    assert len(lua_blocks) == 1
    lua = lua_blocks[0]
    assert lua.get("args") == []
    assert lua.get("children") == []
    assert isinstance(lua.get("raw"), list) and len(lua.get("raw")) == 1
    assert "ngx.location.capture" in lua["raw"][0]


def test_file_delimiters_from_dump():
    config = """
# configuration file /etc/nginx/nginx.conf:
http {
    include sites/*.conf;
}

# configuration file /etc/nginx/sites/default.conf:
server {

}
    """
    nodes = RawParser().parse(config)
    files = [n["file"] for n in nodes if n.get("kind") == "file_delimiter"]
    assert files == ["/etc/nginx/nginx.conf", "/etc/nginx/sites/default.conf"]


def test_inline_comments_filtered_but_standalone_kept():
    config = """
# Standalone
add_header X-Some-Comment some;

if (1) # Inline
{
    add_header X-Inline blank;
}
    """
    nodes = RawParser().parse(config)
    texts = [n.get("text") for n in nodes if n.get("kind") == "comment"]
    assert "Standalone" in texts
    # Inline comment should not appear as a standalone comment node
    assert not any(t and "Inline" in t for t in texts)


def test_braced_variable_args_split():
    """
    Regression test for braced variable tokenization.

    Prior to ngxparse 0.5.16, crossplane incorrectly tokenized
    'map ${var1}${var2} $result' as having a single arg '${var1}${var2} $result'
    instead of two separate args. This test ensures the fix works correctly.
    """
    config = """
http {
    map ${detect_bot}${geo_list} $intermed {
        default 0;
    }
}
    """
    nodes = RawParser().parse(config)

    # Find the map block
    def find_blocks(ns, name):
        for x in ns:
            if x.get("name") == name and x.get("kind") == "block":
                yield x
            if x.get("kind") == "block":
                yield from find_blocks(x.get("children", []), name)

    map_blocks = list(find_blocks(nodes, "map"))
    assert len(map_blocks) == 1
    map_block = map_blocks[0]

    # Args should be split correctly: ['${detect_bot}${geo_list}', '$intermed']
    assert len(map_block.get("args", [])) == 2
    assert map_block["args"][0] == "${detect_bot}${geo_list}"
    assert map_block["args"][1] == "$intermed"
