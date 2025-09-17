# 🛠️ Guía de Instalación Paso a Paso

## Control de Tablillas - Alsina Forms Co.

Esta guía te llevará paso a paso para instalar y ejecutar la aplicación de control de tablillas.

---

## 📋 Prerrequisitos

### 1. Verificar Python
Abrir **Command Prompt** (cmd) o **Terminal** y ejecutar:
```bash
python --version
```
Debe mostrar Python 3.8 o superior. Si no tienes Python instalado:
- Descargar desde: https://www.python.org/downloads/
- ✅ Durante la instalación, marcar "Add Python to PATH"

### 2. Verificar pip
```bash
pip --version
```
Si no está disponible, instalar con:
```bash
python -m ensurepip --upgrade
```

---

## 📁 Paso 1: Preparar Archivos

### Crear directorio del proyecto:
```bash
mkdir control-tablillas
cd control-tablillas
```

### Guardar los siguientes archivos en el directorio:

1. **app.py** - Aplicación principal Streamlit
2. **pdf_parser.py** - Parser especializado para PDFs
3. **run_app.py** - Script de inicio
4. **requirements.txt** - Lista de dependencias
5. **config.json** - Archivo de configuración
6. **README.md** - Manual de usuario

---

## 🔧 Paso 2: Instalar Dependencias

### Opción A: Instalación automática
```bash
pip install -r requirements.txt
```

### Opción B: Instalación manual (si la anterior falla)
```bash
pip install streamlit==1.28.1
pip install pandas==2.1.1
pip install plotly==5.17.0
pip install pdfplumber==0.9.0
pip install openpyxl==3.1.2
pip install xlsxwriter==3.1.9
```

### Verificar instalación:
```bash
pip list | findstr streamlit
```

---

## 🚀 Paso 3: Ejecutar la Aplicación

### Método 1: Script de inicio (Recomendado)
```bash
python run_app.py
```

### Método 2: Directamente con Streamlit
```bash
streamlit run app.py
```

### Método 3: Con puerto personalizado
```bash
streamlit run app.py --server.port=8502
```

---

## 🌐 Paso 4: Acceder a la Aplicación

1. La aplicación se abrirá automáticamente en tu navegador
2. Si no se abre, ve a: `http://localhost:8501`
3. Deberías ver la pantalla principal con el título "Control de Tablillas"

---

## 📊 Paso 5: Probar con Datos

### Preparar archivo PDF de prueba:
1. Usar el archivo PDF del reporte ERP de Alsina Forms
2. En la aplicación, hacer clic en "Browse files" en la barra lateral
3. Seleccionar el archivo PDF
4. La aplicación procesará automáticamente los datos

---

## ⚠️ Solución de Problemas Comunes

### Error: "streamlit no se reconoce como comando"
**Solución:**
```bash
python -m streamlit run app.py
```

### Error: "No module named 'streamlit'"
**Solución:**
```bash
pip install --user streamlit
```

### Error: "Permission denied"
**En Windows:** Ejecutar Command Prompt como Administrador
**En Mac/Linux:** Usar `sudo` antes del comando

### Error: "Puerto en uso"
**Solución:**
```bash
streamlit run app.py --server.port=8502
```

### Error al procesar PDF
**Verificar:**
- El archivo PDF no está protegido con contraseña
- El archivo contiene texto seleccionable (no es una imagen)
- El formato corresponde al reporte estándar de Alsina Forms

---

## 📱 Paso 6: Uso Básico

### Primera vez:
1. **Cargar PDF**: Usar la barra lateral para subir archivo
2. **Ver Dashboard**: Revisar métricas principales
3. **Explorar Filtros**: Probar análisis detallado
4. **Exportar Datos**: Descargar reporte en Excel

### Uso diario:
1. Cargar reporte PDF matutino
2. Revisar items de alta prioridad
3. Asignar tareas a equipos
4. Monitorear progreso durante el día

---

## 💾 Archivos Generados Automáticamente

La aplicación creará automáticamente:
- `tablillas_history.json` - Historial de reportes
- `data/` - Directorio para archivos temporales
- `exports/` - Archivos Excel exportados
- `logs/` - Logs del sistema

---

## 🔧 Configuración Avanzada

### Personalizar configuración:
Editar el archivo `config.json` para ajustar:
- Pesos de prioridad
- Umbrales de alerta
- Configuración de almacenes
- Opciones de exportación

### Ejemplo de personalización:
```json
{
  "priority_weights": {
    "days_since_return": 0.5,
    "counting_delay": 0.3,
    "validation_delay": 0.15,
    "open_tablets": 0.05
  }
}
```

---

## 📞 Obtener Ayuda

### Si encuentras problemas:
1. **Revisar logs**: Buscar mensajes de error en la terminal
2. **Verificar archivos**: Asegurar que todos los archivos .py están en el directorio
3. **Reinstalar**: Eliminar directorio y volver a instalar
4. **Contactar soporte**: enviar captura de pantalla del error

### Información del sistema para soporte:
```bash
python --version
pip --version
streamlit --version
```

---

## 🎯 ¡Listo para Usar!

Si seguiste todos los pasos correctamente, ahora tienes:
- ✅ Aplicación web funcionando
- ✅ Capacidad de procesar PDFs
- ✅ Dashboard interactivo
- ✅ Sistema de prioridades
- ✅ Exportación a Excel
- ✅ Historial de datos

### Próximos pasos:
1. Cargar tu primer reporte PDF
2. Explorar todas las funcionalidades
3. Configurar según tus necesidades específicas
4. Entrenar a tu equipo en el uso de la herramienta

---

**¡Felicidades! Ya tienes tu sistema de control de tablillas operativo. 🎉**