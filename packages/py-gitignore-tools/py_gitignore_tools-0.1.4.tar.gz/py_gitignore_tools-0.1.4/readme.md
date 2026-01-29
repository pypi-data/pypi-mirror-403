# py-gitignore-tools 🐍

Generador de archivos `.gitignore` automáticos para entornos de Python. Evita subir archivos basura, cachés y secretos de producción (`.env`) a tu repositorio con un solo comando.

## ✨ Características

- 🚀 **Específico para Python:** Incluye reglas para Pycache, librerías instaladas y archivos de compilación.
- 🌐 **Soporte Frameworks:** Reglas preconfiguradas para **Django, Flask y FastAPI**.
- 🛡️ **Seguridad:** Bloquea automáticamente archivos de entorno (.env, .venv) y bases de datos locales (sqlite3).
- 🛠️ **Minimalista:** Sin dependencias pesadas.

## 🚀 Instalación
Ejecuta el siguiente comando para instalar el paquete desde [PyPI](https://pypi.org):

```bash
pip install py-gitignore-tools
```

Después de instalarlo, ejecuta el comando en la raíz de tu proyecto para generar el archivo `.gitignore`:

```bash
py-gitignore            # crea un .gitignore en el directorio actual
```
