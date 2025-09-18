# 🏭 Sistema de Control de Tablillas - Versión Local

## 📋 Descripción

Versión local del Sistema Profesional de Control de Tablillas de Alsina Forms Co. Esta versión está optimizada para ejecutarse en tu computadora local con todas las funcionalidades completas.

## 🚀 Instalación Local

### 📋 Requisitos del Sistema

#### **Sistema Operativo:**
- ✅ **Windows 10/11** (recomendado)
- ✅ **macOS 10.15+** 
- ✅ **Linux Ubuntu 18.04+**

#### **Python:**
- ✅ **Python 3.11.9** (recomendado)
- ✅ **Python 3.10.x** (compatible)
- ✅ **Python 3.9.x** (compatible)

#### **Memoria RAM:**
- ✅ **Mínimo:** 4GB RAM
- ✅ **Recomendado:** 8GB+ RAM

#### **Espacio en Disco:**
- ✅ **Mínimo:** 2GB espacio libre
- ✅ **Recomendado:** 5GB+ espacio libre

### 🛠️ Instalación Paso a Paso

#### **1. Verificar Python**
```bash
python --version
# Debe mostrar Python 3.9+ o superior
```

#### **2. Crear Entorno Virtual (Recomendado)**
```bash
# Crear entorno virtual
python -m venv control_tablillas_env

# Activar entorno virtual
# Windows:
control_tablillas_env\Scripts\activate
# macOS/Linux:
source control_tablillas_env/bin/activate
```

#### **3. Instalar Dependencias**
```bash
# Instalar todas las dependencias
pip install -r requirements_local.txt

# Verificar instalación
pip list
```

#### **4. Instalar Ghostscript (Requerido para Camelot)**

**Windows:**
1. Descargar Ghostscript desde: https://www.ghostscript.com/download/gsdnld.html
2. Instalar con configuración por defecto
3. Agregar a PATH del sistema

**macOS:**
```bash
# Con Homebrew
brew install ghostscript

# Con MacPorts
sudo port install ghostscript
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install ghostscript
```

#### **5. Verificar Instalación**
```bash
# Verificar Ghostscript
gs --version

# Verificar Python
python -c "import streamlit, pandas, camelot; print('✅ Todas las dependencias instaladas correctamente')"
```

## 🚀 Ejecución Local

### **Iniciar la Aplicación**
```bash
# Desde el directorio del proyecto
streamlit run app_local.py

# O con configuración específica
streamlit run app_local.py --server.port 8501 --server.address localhost
```

### **Acceder a la Aplicación**
- 🌐 **URL Local:** http://localhost:8501
- 🌐 **URL Red:** http://[TU_IP]:8501 (para acceso desde otros dispositivos)

## 📊 Funcionalidades Completas

### **📄 Procesamiento de PDF**
- ✅ Extracción automática con Camelot
- ✅ Corrección de columnas concatenadas
- ✅ Normalización de códigos de almacén
- ✅ Análisis visual con gráficos

### **📈 Análisis Multi-Excel**
- ✅ Comparación entre múltiples archivos
- ✅ Detección de albaranes cerrados/nuevos
- ✅ Análisis de tendencias temporales
- ✅ Dashboard ejecutivo profesional

### **📋 Informes Profesionales**
- ✅ Exportación a Excel con formato ejecutivo
- ✅ Múltiples hojas con análisis detallado
- ✅ Gráficos significativos y métricas
- ✅ Descarga directa sin afectar dashboard

### **🎨 Interfaz Visual**
- ✅ Dashboard ejecutivo con cards profesionales
- ✅ Gráficos interactivos con Plotly
- ✅ Colores corporativos y diseño moderno
- ✅ Métricas de evolución automáticas

## 🔧 Configuración Avanzada

### **Puerto Personalizado**
```bash
streamlit run app_local.py --server.port 8080
```

### **Acceso desde Red Local**
```bash
streamlit run app_local.py --server.address 0.0.0.0
```

### **Configuración de Rendimiento**
```bash
# Para archivos PDF grandes
streamlit run app_local.py --server.maxUploadSize 200
```

## 🛠️ Solución de Problemas

### **Error: "Ghostscript not found"**
```bash
# Verificar instalación
gs --version

# Si no está instalado, instalar según tu sistema operativo
# Ver sección de instalación de Ghostscript arriba
```

### **Error: "Module not found"**
```bash
# Reinstalar dependencias
pip install -r requirements_local.txt --force-reinstall
```

### **Error: "Permission denied"**
```bash
# En Windows, ejecutar como administrador
# En macOS/Linux, verificar permisos de archivos
chmod +x app_local.py
```

### **Error: "Port already in use"**
```bash
# Usar puerto diferente
streamlit run app_local.py --server.port 8502
```

### **PDF no se procesa correctamente**
1. Verificar que Ghostscript esté instalado
2. Verificar que el PDF no esté corrupto
3. Probar con PDF más simple primero

## 📁 Estructura de Archivos

```
control-tablillas-local/
├── app_local.py              # 🏭 Aplicación principal
├── requirements_local.txt    # 📦 Dependencias para local
├── README_LOCAL.md          # 📚 Este archivo
├── install_local.py         # 🔧 Script de instalación automática
├── run_local.py             # 🚀 Script de inicio rápido
├── start_local.bat          # 🪟 Script para Windows
├── start_local.sh           # 🐧 Script para macOS/Linux
├── .streamlit/
│   └── config.toml          # ⚙️ Configuración de Streamlit
├── .vscode/
│   ├── launch.json          # 🎯 Configuración de debug VS Code
│   └── tasks.json           # 📋 Tareas personalizadas VS Code
├── .gitignore               # 🚫 Archivos a ignorar
└── data/                    # 📁 Carpeta para archivos de prueba
    └── README_DATA.md       # 📝 Documentación de datos
```

## 🎯 Uso Rápido

### **1. Procesar PDF:**
1. Abrir http://localhost:8501
2. Ir a pestaña "PROCESAR PDF"
3. Subir archivo PDF
4. Ver resultados y gráficos
5. Exportar a Excel

### **2. Análisis Multi-Excel:**
1. Ir a pestaña "ANÁLISIS MULTI-EXCEL"
2. Subir múltiples archivos Excel
3. Ver dashboard ejecutivo
4. Analizar tendencias
5. Exportar informes

## 🔒 Seguridad Local

- ✅ **Procesamiento local** - Todos los datos se procesan en tu computadora
- ✅ **Sin conexión a internet** requerida para funcionamiento
- ✅ **Sin almacenamiento** permanente de datos
- ✅ **Control total** sobre tus archivos

## 📞 Soporte

### **Problemas Comunes:**
1. **Ghostscript no encontrado** → Instalar Ghostscript
2. **Dependencias faltantes** → `pip install -r requirements_local.txt`
3. **Puerto ocupado** → Cambiar puerto con `--server.port`
4. **PDF no procesa** → Verificar formato y Ghostscript

### **Logs y Debug:**
```bash
# Ejecutar con logs detallados
streamlit run app_local.py --logger.level debug
```

## 🚀 Ventajas de la Versión Local

- ✅ **Rendimiento superior** - Sin limitaciones de servidor
- ✅ **Privacidad total** - Datos nunca salen de tu computadora
- ✅ **Sin límites** - Procesa archivos de cualquier tamaño
- ✅ **Control completo** - Personalizable según necesidades
- ✅ **Sin costos** - Ejecución completamente gratuita
- ✅ **Offline** - Funciona sin conexión a internet

---

**🎯 ¡Listo para usar! Ejecuta `streamlit run app_local.py` y comienza a analizar tus tablillas localmente.**

**Desarrollado con ❤️ para Alsina Forms Co. - Versión Local Optimizada**