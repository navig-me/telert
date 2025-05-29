
# telert – Alertas para tu terminal

[English](README.md) | [हिन्दी](README.hi.md) | [中文 (简体)](README.zh-CN.md) | [Español](README.es.md)

<p align="center">
  <img src="https://github.com/navig-me/telert/raw/main/telert.png" alt="telert logo" width="150">
</p>

**Versión 0.2.1**

[![GitHub Stars](https://img.shields.io/github/stars/navig-me/telert?style=social)](https://github.com/navig-me/telert/stargazers)
[![PyPI version](https://img.shields.io/pypi/v/telert)](https://pypi.org/project/telert/)
[![Downloads](https://static.pepy.tech/personalized-badge/telert?period=month&units=international_system&left_color=grey&right_color=blue&left_text=downloads)](https://pepy.tech/project/telert)
[![License](https://img.shields.io/github/license/navig-me/telert)](https://github.com/navig-me/telert/blob/main/docs/LICENSE)
[![Marketplace](https://img.shields.io/badge/GitHub%20Marketplace-Use%20this%20Action-blue?logo=github)](https://github.com/marketplace/actions/telert-run)
[![VS Code Marketplace](https://vsmarketplacebadges.dev/version/Navig.telert-vscode.svg?subject=VS%20Code%20Marketplace&style=flat-square)](https://marketplace.visualstudio.com/items?itemName=Navig.telert-vscode)

## 📱 Descripción general

Telert es una herramienta ligera que envía notificaciones cuando tus comandos de terminal o código en Python terminan de ejecutarse. Soporta múltiples canales de notificación:

- **Aplicaciones de mensajería**: Telegram, Microsoft Teams, Slack, Discord
- **Correo electrónico**: Email
- **Dispositivos móviles**: Pushover (para Android e iOS)
- **Notificaciones locales**: Notificaciones de escritorio, alertas de audio
- **Integraciones personalizadas**: Puntos finales HTTP para cualquier servicio

Ideal para tareas de larga duración, servidores remotos, pipelines de CI o monitoreo de código crítico.

Disponible como:
- Paquete de Python: `pip install telert`
- Imagen de Docker: `docker pull ghcr.io/navig-me/telert:latest`
- API en la nube alojada en Replit, Railway, Render o Fly.io

<img src="https://github.com/navig-me/telert/raw/main/docs/telert-demo.svg" alt="telert demo" width="600">

## 🚀 Instalación y Comienzo Rápido

```bash
pip install telert
telert init
```

### Beneficios clave

- 📱 Recibe notificaciones cuando los comandos finalicen, incluso si estás lejos de tu equipo
- ⏱️ Mide exactamente cuánto tardó tu comando o código
- 🚦 Captura el código de estado de éxito/fallo y cualquier error
- 📃 Visualiza fragmentos de salida del comando en la notificación
- 🔄 Funciona con comandos shell, tuberías y código en Python


## 🚦 Monitorización

### Monitorización de Procesos

Supervise el uso de recursos de procesos y reciba notificaciones cuando excedan los umbrales:

```bash
# Monitorear uso de memoria de un proceso
telert monitor process --name "mi_app" --command "ps aux | grep mi_app" --memory-threshold 2G

# Monitorear múltiples procesos
telert monitor process --name "servicios" --command "ps aux | grep -E 'nginx|postgres'" --cpu-threshold 80

# Listar todos los monitores de procesos
telert monitor process --list

# Detener monitoreo de un proceso
telert monitor process --stop <id-monitor>
```

### Monitorización de Archivos de Log

Vigile archivos de registro en busca de patrones específicos y reciba notificaciones con contexto cuando se encuentren coincidencias:

```bash
# Monitorear un archivo de log para patrones
telert monitor log --file "/var/log/aplicacion.log" --pattern "ERROR|CRITICO" --provider telegram

# Monitoreo avanzado con contexto
telert monitor log \
  --file "/var/log/nginx/error.log" \
  --pattern ".*\[error\].*" \
  --context-lines 5 \
  --cooldown 300 \
  --provider slack

# Listar todos los monitores de log
telert monitor log --list
```

### Monitorización de Red

Supervise la conectividad de red y servicios con diferentes tipos de verificación:

```bash
# Monitoreo básico de ping
telert monitor network --host ejemplo.com --type ping --interval 60 --provider slack

# Monitoreo de punto final HTTP
telert monitor network \
  --url https://api.ejemplo.com/health \
  --expected-status 200 \
  --timeout 5 \
  --provider telegram

# Monitoreo de puerto TCP
telert monitor network --host db.ejemplo.com --port 5432 --provider email

# Listar todos los monitores de red
telert monitor network --list
```

Para documentación detallada sobre las características de monitoreo, consulte la [Guía de Monitoreo](https://github.com/navig-me/telert/blob/main/docs/MONITORING.md).

## 🤝 Contribuciones / Licencia

¡Se aceptan PRs y sugerencias!  
Licenciado bajo MIT – consulta el archivo `LICENSE`.

## 👏 Agradecimientos

Este proyecto ha sido mejorado gracias a todos los colaboradores que brindan sugerencias y comentarios. Si esta herramienta te resulta útil, considera [apoyar el proyecto en Buy Me a Coffee](https://www.buymeacoffee.com/mihirk) ☕

### ¿Necesitas un VPS?

Prueba estos proveedores con créditos gratuitos:

- [Vultr](https://www.vultr.com/?ref=9752934-9J) — $100 en créditos gratis
- [DigitalOcean](https://m.do.co/c/cdf2b5a182f2) — $200 en créditos gratis
