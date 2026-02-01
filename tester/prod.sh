[Unit]
Description=Servicio para ejecutar mi script de Bash
After=network.target

[Service]
# Ejecutar como root (por defecto systemd corre como root si no se especifica User)
User=root
Group=root

# Tipo de servicio: 'oneshot' si el script hace algo y termina, 
# o 'simple' si el script se queda corriendo (como un servidor)
Type=simple

# Ruta absoluta al script
ExecStart=/bin/bash /ruta/completa/a/tu/script.sh

# Reiniciar automáticamente si falla
Restart=on-failure

# Directorio de trabajo
WorkingDirectory=/ruta/completa/a/donde_esta_el_script

[Install]
WantedBy=multi-user.target
