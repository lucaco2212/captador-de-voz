"""Punto de entrada para la aplicación de captura de voz de pedidos FRUNA."""

from ui.app_ui import AppUI


def main() -> None:
    """Inicializa y ejecuta la interfaz principal."""
    app = AppUI()
    app.run()


if __name__ == "__main__":
    main()
