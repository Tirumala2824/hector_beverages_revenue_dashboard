def test_application_composition_root_is_importable():
    from app.main import app

    assert app.title == "Revenue Performance Dashboard"
    assert any(route.path == "/" for route in app.routes)
