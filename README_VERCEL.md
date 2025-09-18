# 🏗️ Sistema Profesional de Control de Tablillas - Vercel

## 🚀 Despliegue en Vercel

### ✅ **Ventajas de Vercel sobre Streamlit:**

- ✅ **Camelot funciona perfectamente** - Soporte completo para OpenCV y Ghostscript
- ✅ **Más rápido** - Serverless functions optimizadas
- ✅ **Más confiable** - Infraestructura de Vercel
- ✅ **Gratis** - Para proyectos pequeños
- ✅ **Deploy automático** - Desde GitHub

### 📋 **Pasos para Desplegar:**

#### 1. **Preparar el Repositorio**
```bash
# Asegúrate de que estos archivos estén en tu repo:
- app.py (aplicación principal)
- requirements.txt (dependencias)
- vercel.json (configuración)
- package.json (metadatos)
```

#### 2. **Conectar con Vercel**
1. Ve a [vercel.com](https://vercel.com)
2. Conecta tu cuenta de GitHub
3. Importa el repositorio `ControlTablillas`
4. Vercel detectará automáticamente la configuración

#### 3. **Configuración Automática**
Vercel detectará:
- ✅ `vercel.json` - Configuración de Python
- ✅ `requirements.txt` - Dependencias
- ✅ `app.py` - Archivo principal

#### 4. **Deploy Automático**
- ✅ Cada push a `main` = deploy automático
- ✅ Camelot se instala correctamente
- ✅ OpenCV y Ghostscript funcionan
- ✅ Aplicación disponible en `https://tu-app.vercel.app`

### 🔧 **Configuración Técnica:**

#### **vercel.json**
```json
{
  "version": 2,
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ],
  "functions": {
    "app.py": {
      "maxDuration": 30
    }
  }
}
```

#### **requirements.txt**
```
streamlit>=1.28.0
pandas>=2.0.0
plotly>=5.15.0
openpyxl>=3.1.0
xlsxwriter>=3.1.0
camelot-py[cv]>=0.10.1
opencv-python>=4.8.0
ghostscript>=0.7
```

### 🎯 **Funcionalidades Completas:**

#### **📄 Procesar PDF**
- ✅ **Camelot** para extracción perfecta de tablas
- ✅ **Métodos Stream y Lattice** para diferentes tipos de PDF
- ✅ **Análisis de prioridades** con métricas avanzadas
- ✅ **Generación de Excel** con múltiples hojas

#### **📊 Análisis Multi-Excel**
- ✅ **Comparación día a día** de archivos Excel
- ✅ **Detección de cambios** en albaranes y tablillas
- ✅ **Evolución temporal** con gráficos interactivos
- ✅ **Resúmenes automáticos** de tendencias

### 🐪 **Camelot en Vercel:**

Vercel soporta **completamente** Camelot porque:
- ✅ **OpenCV** se instala correctamente
- ✅ **Ghostscript** funciona sin problemas
- ✅ **Dependencias del sistema** están disponibles
- ✅ **Tiempo de ejecución** suficiente para procesamiento

### 🚀 **Comandos de Deploy:**

```bash
# 1. Subir cambios
git add .
git commit -m "🚀 Deploy para Vercel con Camelot"
git push origin main

# 2. Vercel detectará automáticamente y desplegará
# 3. Tu app estará disponible en: https://tu-app.vercel.app
```

### 📊 **Monitoreo:**

- ✅ **Logs en tiempo real** en dashboard de Vercel
- ✅ **Métricas de performance** automáticas
- ✅ **Alertas** si hay errores
- ✅ **Rollback automático** si algo falla

### 🎉 **Resultado Final:**

Una aplicación **profesional** con:
- 🐪 **Camelot funcionando perfectamente**
- 📄 **Extracción PDF precisa**
- 📊 **Análisis multi-Excel completo**
- 🚀 **Deploy automático desde GitHub**
- ⚡ **Performance optimizada**

**¡Vercel es la solución perfecta para tu aplicación!** 🎯