from v1 import create_app as crear_app_v1
from v2 import registrar_v2


def create_app(config_name=None):
    app = crear_app_v1(config_name)
    registrar_v2(app)
    return app


app = create_app()

if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port)
