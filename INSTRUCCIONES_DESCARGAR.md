# 🚀 INSTRUCCIONES PARA DESCARGAR Y EJECUTAR

## 📥 **PASO 1: DESCARGAR EL REPOSITORIO**

### **Opción A: Descargar ZIP (Más Fácil)**
1. **Ir a:** https://github.com/Sinsapiar1/ControlTablillas
2. **Click en:** "Code" → "Download ZIP"
3. **Extraer** el archivo ZIP en tu computadora
4. **Entrar** a la carpeta `ControlTablillas-main`

### **Opción B: Con Git (Si tienes Git instalado)**
```bash
git clone https://github.com/Sinsapiar1/ControlTablillas.git
cd ControlTablillas
git checkout local-version
```

## 🐍 **PASO 2: VERIFICAR PYTHON**

### **Verificar si tienes Python:**
```bash
python --version
```
**Debe mostrar:** Python 3.9 o superior

### **Si NO tienes Python:**
- **Descargar:** https://www.python.org/downloads/
- **Instalar** con "Add to PATH" marcado
- **Reiniciar** la computadora

## 📦 **PASO 3: INSTALAR DEPENDENCIAS**

### **Abrir Terminal/CMD en la carpeta del proyecto:**

**Windows:**
- **Click derecho** en la carpeta → "Abrir en Terminal"
- **O** Shift + Click derecho → "Abrir ventana de PowerShell aquí"

**macOS/Linux:**
- **Click derecho** en la carpeta → "Abrir Terminal aquí"

### **Ejecutar comando:**
```bash
pip install -r requirements_local.txt
```

**Si da error, probar:**
```bash
python -m pip install -r requirements_local.txt
```

## 🔧 **PASO 4: INSTALAR GHOSTSCRIPT (REQUERIDO)**

### **Windows:**
1. **Descargar:** https://www.ghostscript.com/download/gsdnld.html
2. **Instalar** con configuración por defecto
3. **Reiniciar** terminal/CMD

### **macOS:**
```bash
brew install ghostscript
```

### **Linux (Ubuntu/Debian):**
```bash
sudo apt-get install ghostscript
```

## 🚀 **PASO 5: EJECUTAR LA APLICACIÓN**

### **Comando principal:**
```bash
streamlit run app_local.py
```

### **Si da error, probar:**
```bash
python -m streamlit run app_local.py
```

## 🌐 **PASO 6: ABRIR EN NAVEGADOR**

- **Se abre automáticamente** en: http://localhost:8501
- **Si no se abre:** Copiar y pegar la URL en el navegador

## ⏹️ **PASO 7: DETENER LA APLICACIÓN**

- **Presionar:** Ctrl + C en la terminal
- **O** Cerrar la ventana de la terminal

---

## 🎯 **RESUMEN RÁPIDO:**

1. **📥 Descargar** ZIP del repositorio
2. **🐍 Verificar** Python 3.9+
3. **📦 Instalar** dependencias: `pip install -r requirements_local.txt`
4. **🔧 Instalar** Ghostscript
5. **🚀 Ejecutar:** `streamlit run app_local.py`
6. **🌐 Abrir:** http://localhost:8501

---

## 🛠️ **SOLUCIÓN DE PROBLEMAS:**

### **Error: "streamlit not found"**
```bash
pip install streamlit
```

### **Error: "Ghostscript not found"**
- Instalar Ghostscript según tu sistema operativo

### **Error: "Port already in use"**
```bash
streamlit run app_local.py --server.port 8502
```

### **Error: "Permission denied"**
- **Windows:** Ejecutar CMD como administrador
- **macOS/Linux:** `chmod +x app_local.py`

---

## 📞 **¿NECESITAS AYUDA?**

### **Problemas comunes:**
1. **Python no encontrado** → Instalar Python
2. **Dependencias no se instalan** → `pip install --upgrade pip`
3. **Ghostscript no funciona** → Reinstalar Ghostscript
4. **Puerto ocupado** → Cambiar puerto

### **Verificar instalación:**
```bash
python -c "import streamlit, pandas, camelot; print('✅ Todo instalado correctamente')"
```

---

**🎉 ¡LISTO! Ahora puedes usar la aplicación de Control de Tablillas en tu computadora local.**