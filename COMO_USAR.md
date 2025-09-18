# 🏭 CONTROL DE TABLILLAS - CÓMO USAR

## 🎯 **¿QUÉ HACE ESTA APLICACIÓN?**

- ✅ **Procesa archivos PDF** de tablillas automáticamente
- ✅ **Analiza archivos Excel** y compara fechas
- ✅ **Genera informes** profesionales en Excel
- ✅ **Muestra gráficos** y estadísticas
- ✅ **Funciona en tu computadora** sin internet

## 📋 **PASOS MUY SIMPLES:**

### **1️⃣ DESCARGAR**
- **Ir a:** https://github.com/Sinsapiar1/ControlTablillas
- **Click:** "Code" → "Download ZIP"
- **Extraer** el archivo en tu escritorio

### **2️⃣ INSTALAR PYTHON**
- **Ir a:** https://www.python.org/downloads/
- **Descargar** Python (versión más reciente)
- **Instalar** marcando "Add to PATH"
- **Reiniciar** la computadora

### **3️⃣ INSTALAR GHOSTSCRIPT**
- **Ir a:** https://www.ghostscript.com/download/gsdnld.html
- **Descargar** Ghostscript
- **Instalar** con configuración por defecto

### **4️⃣ ABRIR TERMINAL**
- **Windows:** Click derecho en la carpeta → "Abrir en Terminal"
- **macOS:** Click derecho → "Abrir Terminal aquí"

### **5️⃣ INSTALAR DEPENDENCIAS**
**Escribir en terminal:**
```
pip install -r requirements_local.txt
```

### **6️⃣ EJECUTAR APLICACIÓN**
**Escribir en terminal:**
```
streamlit run app_local.py
```

### **7️⃣ ABRIR NAVEGADOR**
- **Se abre automáticamente** en: http://localhost:8501
- **Si no se abre:** Copiar la URL en el navegador

---

## 🎮 **CÓMO USAR LA APLICACIÓN:**

### **📄 PROCESAR PDF:**
1. **Ir a pestaña:** "PROCESAR PDF"
2. **Subir archivo** PDF de tablillas
3. **Esperar** a que procese
4. **Ver resultados** y gráficos
5. **Descargar** informe en Excel

### **📊 ANALIZAR EXCEL:**
1. **Ir a pestaña:** "ANÁLISIS MULTI-EXCEL"
2. **Subir varios archivos** Excel de diferentes fechas
3. **Ver dashboard** con estadísticas
4. **Analizar tendencias** y cambios
5. **Descargar** informes profesionales

---

## 🛠️ **SI ALGO NO FUNCIONA:**

### **❌ Error: "Python no encontrado"**
- **Solución:** Instalar Python desde python.org

### **❌ Error: "streamlit not found"**
- **Solución:** Escribir en terminal: `pip install streamlit`

### **❌ Error: "Ghostscript not found"**
- **Solución:** Instalar Ghostscript desde ghostscript.com

### **❌ Error: "Port already in use"**
- **Solución:** Escribir: `streamlit run app_local.py --server.port 8502`

### **❌ La aplicación no se abre**
- **Solución:** Abrir navegador y ir a: http://localhost:8501

---

## 📞 **¿NECESITAS AYUDA?**

### **Verificar que todo esté bien:**
**Escribir en terminal:**
```
python -c "import streamlit, pandas, camelot; print('✅ Todo funciona correctamente')"
```

### **Si aparece "✅ Todo funciona correctamente":**
- **¡Perfecto!** La aplicación está lista para usar

### **Si aparece error:**
- **Revisar** los pasos de instalación
- **Instalar** las dependencias faltantes

---

## 🎯 **RESUMEN:**

1. **📥 Descargar** ZIP del repositorio
2. **🐍 Instalar** Python
3. **🔧 Instalar** Ghostscript
4. **📦 Instalar** dependencias: `pip install -r requirements_local.txt`
5. **🚀 Ejecutar:** `streamlit run app_local.py`
6. **🌐 Abrir:** http://localhost:8501

**¡Y listo! Ya puedes usar la aplicación de Control de Tablillas.**

---

**💡 TIP:** Si tienes problemas, revisa que Python y Ghostscript estén instalados correctamente.