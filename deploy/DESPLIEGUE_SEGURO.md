# Despliegue seguro de la API (V-03)

El reporte marcó que la API se publica desde una máquina personal con Tailscale Funnel.
Mientras se consigue un servidor dedicado (VPS), estas medidas reducen el riesgo:

## 1. Servicio aislado (usuario sin privilegios)

```bash
cd ~/ApiDevRootDark          # tu carpeta del repo en el servidor
git pull origin api
sudo bash deploy/instalar_seguro.sh
```

Qué hace:

- Crea el usuario de sistema `devrootdark` (sin shell, sin acceso a `/home`).
- Copia el código a `/opt/devrootdark/api` (el servicio solo puede leerlo).
- Copia `uploads/`, `backups/` y `comprobantes/` a `/var/lib/devrootdark/` (lo único donde puede escribir).
- Instala `apidevrootdark.service` con aislamiento de systemd: `NoNewPrivileges`, `ProtectSystem=strict`,
  `ProtectHome`, `PrivateTmp`, sin capacidades especiales.
- La API escucha **solo en 127.0.0.1:5000**: nadie de la red local entra directo.

Para actualizar después: `git pull origin api && sudo bash deploy/instalar_seguro.sh`
(ya lo hace `scripts/actualizar_servidor.sh`).

Comprobar el aislamiento: `systemd-analyze security apidevrootdark` (debe salir en verde/amarillo, "OK" o "MEDIUM").

## 2. Tailscale Funnel: solo la API

```bash
tailscale funnel status          # lo que está publicado en internet
sudo tailscale funnel reset      # si aparece algo que no sea la API
sudo tailscale funnel --bg 5000  # publica únicamente el puerto 5000
```

Jellyfin (8096), SSH (22) y cualquier otro servicio **no** deben aparecer en `funnel status`.
Para verlos fuera de casa usa `tailscale serve` (solo tus dispositivos) en lugar de Funnel.

## 3. Firewall de la máquina

```bash
sudo ufw default deny incoming
sudo ufw allow in on tailscale0      # tus dispositivos de Tailscale
sudo ufw allow from 192.168.0.0/16 to any port 22 proto tcp   # SSH solo desde tu red local
sudo ufw enable
```

## 4. Pendientes fuera del código

- Borrar el sitio viejo `darling-scone-5f7dba.netlify.app` en Netlify (sigue publicado con la versión vulnerable).
- Cambiar la contraseña del usuario de MongoDB Atlas y la `JWT_SECRET_KEY` del `.env`
  (cerrará todas las sesiones abiertas).
- En Netlify: confirmar que existe `VITE_API_URL` en *Site configuration → Environment variables*
  (sin ella la compilación ahora se detiene a propósito).
- A futuro: mover la API a un VPS (Railway, Render, DigitalOcean) para no exponer la máquina de casa.
