# 🌊 Leviathan-UI: Framework Premium para PyQt5 (v1.0.3)

[![Version](https://img.shields.io/badge/version-1.0.3-orange.svg)](https://github.com/JesusQuijada34/leviathan-ui)

**Leviathan-UI** es un framework diseñado para llevar la estética moderna de Windows 11 a tus aplicaciones PyQt5. 

### 🌍 Novedades v1.0.3: Soporte Multilingüe (i18n)
Esta versión introduce un sistema de internacionalización robusto:
- **Autodetección de Idioma**: El framework detecta automáticamente el idioma de tu sistema operativo.
- **Packs de Idioma (`.lv-lng`)**: Soporte para más de 10 regiones, incluyendo Español (AR/MX), Inglés, Árabe, Chino, Japonés, Ruso y más.
- **Seguridad Regional**: Si no se encuentra un pack compatible, el sistema se protege y notifica al usuario en inglés antes de cerrar.

### ✨ Mejoras en el Instalador
- **Splash UWP**: El asistente de instalación ahora inicia con una pantalla de carga moderna estilo Windows.
- **Iconografía SVG Animada**: Cada paso de la instalación cuenta con iconos vectoriales dinámicos.
- **Instalación Local (`dist/`)**: Capacidad para instalar archivos `.whl` directamente desde la carpeta de distribución.

---

## 🛠 Instalación
Ejecuta el asistente visual para una experiencia guiada y multilenguaje:
```bash
python leviathan_installer_gui.py
```
