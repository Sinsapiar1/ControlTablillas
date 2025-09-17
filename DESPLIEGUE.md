# 🚀 Guía de Despliegue - Control de Tablillas

## ✅ Problema Resuelto

**El problema principal era la incompatibilidad de versiones:**
- Python 3.13 no es compatible con pandas 2.1.1
- El sistema tenía un entorno Python "externamente gestionado" que impedía instalar paquetes

## 🔧 Solución Implementada

### 1. Entorno Virtual
Se creó un entorno virtual para aislar las dependencias:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Dependencias Actualizadas
Se actualizó `requirements.txt` con versiones compatibles con Python 3.13:
```
streamlit>=1.28.1
pandas>=2.2.0
plotly>=5.17.0
pdfplumber>=0.9.0
openpyxl>=3.1.2
xlsxwriter>=3.1.9
python-dateutil>=2.8.2
numpy>=1.26.0
pillow>=10.0.1
requests>=2.31.0
```

### 3. Script de Inicio Automatizado
Se creó `start_app.sh` que:
- ✅ Verifica dependencias del sistema
- ✅ Crea entorno virtual si no existe
- ✅ Instala dependencias automáticamente
- ✅ Crea directorios necesarios
- ✅ Inicia la aplicación

## 🚀 Cómo Desplegar

### Opción 1: Script Automático (Recomendado)
```bash
./start_app.sh
```

### Opción 2: Manual
```bash
# 1. Crear entorno virtual
python3 -m venv venv

# 2. Activar entorno
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar aplicación
streamlit run app.py
```

### Opción 3: Con puerto personalizado
```bash
./start_app.sh 8502
```

## 🌐 Acceso a la Aplicación

Una vez iniciada, la aplicación estará disponible en:
- **Local**: http://localhost:8501
- **Red**: http://[IP-DEL-SERVIDOR]:8501

## 📋 Verificación del Despliegue

### 1. Verificar que la aplicación está ejecutándose:
```bash
ps aux | grep streamlit
```

### 2. Verificar que responde:
```bash
curl -s http://localhost:8501 | grep -i streamlit
```

### 3. Verificar logs (si hay errores):
```bash
# Los logs aparecen en la terminal donde se ejecutó la aplicación
```

## 🔍 Solución de Problemas

### Error: "python3-venv no encontrado"
```bash
sudo apt update
sudo apt install python3-venv python3-full
```

### Error: "Puerto en uso"
```bash
# Usar puerto diferente
./start_app.sh 8502
```

### Error: "Permisos denegados"
```bash
chmod +x start_app.sh
```

### Error: "Dependencias no instaladas"
```bash
source venv/bin/activate
pip install -r requirements.txt
```

## 📊 Estado Actual

✅ **Aplicación funcionando correctamente**
- Streamlit ejecutándose en puerto 8501
- Todas las dependencias instaladas
- Entorno virtual configurado
- Script de inicio automatizado creado

## 🎯 Próximos Pasos

1. **Probar la aplicación**: Subir un archivo PDF de prueba
2. **Configurar acceso remoto**: Si necesitas acceso desde otros equipos
3. **Configurar servicio**: Para que se inicie automáticamente al arrancar el servidor
4. **Backup**: Hacer backup de los archivos de configuración

## 📞 Soporte

Si encuentras problemas:
1. Verifica que Python 3.8+ esté instalado
2. Ejecuta `./start_app.sh` y revisa los mensajes de error
3. Verifica que el puerto 8501 esté libre
4. Revisa los logs en la terminal

---

**🎉 ¡La aplicación está lista para usar!**