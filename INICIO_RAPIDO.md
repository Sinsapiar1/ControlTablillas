# ⚡ INICIO RÁPIDO - CONTROL DE TABLILLAS

## 🚀 **PARA USUARIOS AVANZADOS**

### **Instalación en 3 comandos:**
```bash
# 1. Clonar repositorio
git clone https://github.com/Sinsapiar1/ControlTablillas.git
cd ControlTablillas
git checkout local-version

# 2. Instalar dependencias
pip install -r requirements_local.txt

# 3. Ejecutar aplicación
streamlit run app_local.py
```

### **Acceso:** http://localhost:8501

---

## 🛠️ **SCRIPTS AUTOMÁTICOS**

### **Windows:**
```bash
# Doble click en:
start_local.bat
```

### **macOS/Linux:**
```bash
# Ejecutar:
./start_local.sh
```

### **Python directo:**
```bash
# Instalación automática:
python install_local.py

# Inicio con navegador:
python run_local.py
```

---

## 🔧 **CONFIGURACIÓN VS CODE**

### **Si usas Visual Studio Code:**
1. **Abrir** carpeta en VS Code
2. **Presionar F5** para ejecutar
3. **O** Ctrl+Shift+P → "Tasks: Run Task" → "🚀 Start Streamlit App"

---

## 📋 **REQUISITOS MÍNIMOS**

- ✅ **Python 3.9+**
- ✅ **Ghostscript** (para PDF)
- ✅ **4GB RAM**
- ✅ **2GB espacio** en disco

---

## 🎯 **COMANDOS ÚTILES**

### **Verificar instalación:**
```bash
python -c "import streamlit, pandas, camelot; print('✅ OK')"
```

### **Verificar Ghostscript:**
```bash
gs --version
```

### **Cambiar puerto:**
```bash
streamlit run app_local.py --server.port 8502
```

### **Ejecutar en red local:**
```bash
streamlit run app_local.py --server.address 0.0.0.0
```

---

## 🐳 **DOCKER (OPCIONAL)**

### **Si prefieres Docker:**
```bash
# Crear Dockerfile
cat > Dockerfile << EOF
FROM python:3.11-slim
RUN apt-get update && apt-get install -y ghostscript
COPY requirements_local.txt .
RUN pip install -r requirements_local.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app_local.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
EOF

# Construir y ejecutar
docker build -t control-tablillas .
docker run -p 8501:8501 control-tablillas
```

---

## 🔒 **ENTORNO VIRTUAL (RECOMENDADO)**

### **Crear entorno virtual:**
```bash
# Crear entorno
python -m venv control_tablillas_env

# Activar (Windows)
control_tablillas_env\Scripts\activate

# Activar (macOS/Linux)
source control_tablillas_env/bin/activate

# Instalar dependencias
pip install -r requirements_local.txt

# Ejecutar
streamlit run app_local.py
```

---

## 📊 **ESTRUCTURA DEL PROYECTO**

```
ControlTablillas/
├── app_local.py              # 🏭 Aplicación principal
├── requirements_local.txt    # 📦 Dependencias
├── install_local.py         # 🔧 Instalación automática
├── run_local.py             # 🚀 Inicio rápido
├── start_local.bat          # 🪟 Windows
├── start_local.sh           # 🐧 Unix/Linux
├── .streamlit/config.toml   # ⚙️ Configuración
├── .vscode/                 # 🎯 VS Code
└── data/                    # 📁 Datos de prueba
```

---

## 🎯 **RESUMEN EJECUTIVO**

**Para empezar rápido:**
1. `git clone` + `git checkout local-version`
2. `pip install -r requirements_local.txt`
3. `streamlit run app_local.py`
4. Abrir http://localhost:8501

**¡Listo en 2 minutos!**