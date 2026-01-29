import os

import pytest

from fcbyk.web.app import create_spa


def test_create_spa_index_sets_no_cache_headers(monkeypatch, tmp_path):
    # 构造 dist 目录与入口 html
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "slide.html").write_text("<html>ok</html>", encoding="utf-8")

    # 让 create_spa 使用我们临时目录作为 root
    app = create_spa("slide.html", root=str(dist))
    app.config["TESTING"] = True

    client = app.test_client()
    resp = client.get("/")
    assert resp.status_code == 200

    # no-cache headers
    assert resp.headers.get("Cache-Control") == "no-cache, no-store, must-revalidate"
    assert resp.headers.get("Pragma") == "no-cache"
    assert resp.headers.get("Expires") == "0"


def test_create_spa_page_routes(monkeypatch, tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "slide.html").write_text("<html>ok</html>", encoding="utf-8")

    app = create_spa("slide.html", root=str(dist), page=["/a", "/b/c"]) 
    app.config["TESTING"] = True

    client = app.test_client()
    assert client.get("/a").status_code == 200
    assert client.get("/b/c").status_code == 200


def test_create_spa_attaches_cli_data(tmp_path):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "slide.html").write_text("<html>ok</html>", encoding="utf-8")

    app = create_spa("slide.html", root=str(dist), cli_data={"x": 1})
    assert app.cli_data == {"x": 1}

