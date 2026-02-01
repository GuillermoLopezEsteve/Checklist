#!/bin/bash

# --- Configuración ---
SERVICE_NAME="mi_servicio"
SCRIPT_SOURCE="./tu_script_original.sh"
SCRIPT_DEST="/usr/local/bin/mi_script_root.sh"
SERVICE_FILE="/etc/nginx/sites-available/reverse-proxy" # O el nombre que quieras

# --- Funciones de ayuda (las tuyas) ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

fail() { echo -e "${RED}[ERROR  ] $NC$1"; exit 1; }
success() { echo -e "${GREEN}[SUCCESS] $NC$1"; }
pending() { echo -e "${YELLOW}[TRYING ] $NC$1"; }

# --- Validación ---
if [[ $EUID -ne 0 ]]; then
   fail "Este instalador debe ejecutarse con sudo (root)."
fi

# --- Instalación ---

pending "Instalando script de Bash en $SCRIPT_DEST..."
cp "$SCRIPT_SOURCE" "$SCRIPT_DEST" || fail "No se pudo copiar el script."
chmod +x "$SCRIPT_DEST"
chown root:root "$SCRIPT_DEST"
success "Script instalado con permisos seguros."

pending "Creando archivo de unidad de systemd..."
cat <<EOF > /etc/systemd/system/${SERVICE_NAME}.service
[Unit]
Description=Servicio de gestion para alumnos
After=network.target

[Service]
Type=simple
User=root
ExecStart=/bin/bash $SCRIPT_DEST
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

if [ $? -eq 0 ]; then
    success "Archivo .service creado en /etc/systemd/system/${SERVICE_NAME}.service"
else
    fail "Error al crear el archivo de servicio."
fi

pending "Recargando systemd y activando servicio..."
systemctl daemon-reload
systemctl enable ${SERVICE_NAME}.service
systemctl start ${SERVICE_NAME}.service

if systemctl is-active --quiet ${SERVICE_NAME}; then
    success "El servicio está funcionando correctamente como root."
else
    fail "El servicio se instaló pero falló al arrancar. Revisa 'journalctl -u ${SERVICE_NAME}'"
fi
