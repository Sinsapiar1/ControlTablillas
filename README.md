# 🏗️ Control de Tablillas - Alsina Forms Co.

Una herramienta web interactiva para el control y análisis de devoluciones de tablillas, diseñada específicamente para optimizar los procesos operativos de Alsina Forms Co., Inc.

## ✨ Características Principales

- 📄 **Conversión PDF a Excel**: Transformación automática de reportes PDF del ERP
- 🎯 **Sistema de Prioridades**: Algoritmo inteligente basado en fechas y retrasos
- 📊 **Dashboard Interactivo**: Visualizaciones en tiempo real con Plotly
- 📈 **Análisis Predictivo**: Identificación de tendencias y cuellos de botella
- 💾 **Historial JSON**: Seguimiento de progreso diario y comportamiento
- 🏢 **Control por Almacén**: Métricas específicas por ubicación
- 📱 **Interfaz Responsiva**: Optimizada para desktop y móvil

## 🚀 Instalación Rápida

### Requisitos Previos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar o descargar los archivos**
   ```bash
   # Crear directorio del proyecto
   mkdir control-tablillas
   cd control-tablillas
   
   # Colocar todos los archivos .py en este directorio
   ```

2. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar la aplicación**
   ```bash
   python run_app.py
   ```

4. **Acceder a la aplicación**
   - Se abrirá automáticamente en tu navegador
   - URL: `http://localhost:8501`

## 📖 Guía de Uso

### 1. Carga de Datos
1. En la barra lateral, usar "📂 Carga de Datos"
2. Seleccionar el archivo PDF del reporte ERP
3. El sistema procesará automáticamente los datos

### 2. Dashboard Principal
- **Métricas Clave**: Resumen ejecutivo de estado actual
- **Gráficos Interactivos**: Visualización de prioridades y tendencias
- **Tabla de Alta Prioridad**: Items que requieren atención inmediata

### 3. Análisis Detallado
- **Filtros Avanzados**: Por almacén, prioridad, fechas
- **Estadísticas**: Métricas por almacén y cliente
- **Exportación**: Descarga de datos filtrados

### 4. Historial
- **Seguimiento Temporal**: Ver evolución día a día
- **Comparación**: Análisis de tendencias históricas
- **Datos Persistentes**: Información almacenada en JSON

## 📊 Entendiendo las Columnas

| Columna | Descripción | Importancia |
|---------|-------------|-------------|
| **WH** | Almacén origen | ⭐⭐⭐ Crítico para priorización |
| **Return Date** | Fecha de devolución | ⭐⭐⭐ Base para cálculo de prioridades |
| **Customer Name** | Cliente que devuelve | ⭐⭐ Seguimiento comercial |
| **Job Site Name** | Nombre del proyecto | ⭐⭐ Identificación de obra |
| **Definitive Dev** | Estado de cierre | ⭐⭐⭐ Indicador de completitud |
| **Tablets** | Números de tablillas | ⭐⭐⭐ Control de inventario |
| **Total Open** | Tablillas pendientes | ⭐⭐⭐ Workload pendiente |
| **Counting Delay** | Días de retraso | ⭐⭐⭐ KPI operativo |

## 🎯 Sistema de Prioridades

### Algoritmo de Cálculo
La prioridad se calcula usando una fórmula ponderada:

```
Priority Score = (Días desde retorno × 0.4) + 
                 (Retraso de conteo × 0.3) + 
                 (Retraso validación × 0.2) + 
                 (Tablillas abiertas × 0.1)
```

### Niveles de Prioridad
- 🔴 **Alta (60-100 pts)**: Atención inmediata requerida
- 🟡 **Media (30-59 pts)**: Seguimiento cercano necesario  
- 🟢 **Baja (0-29 pts)**: Dentro de parámetros normales

## 📁 Estructura de Archivos

```
control-tablillas/
├── app.py                 # Aplicación principal Streamlit
├── pdf_parser.py          # Parser especializado para PDFs
├── run_app.py            # Script de inicio
├── requirements.txt       # Dependencias Python
├── config.json           # Configuración de la aplicación
├── tablillas_history.json # Historial de reportes (auto-generado)
├── data/                 # Directorio para archivos temporales
├── exports/              # Directorio para archivos exportados
└── logs/                 # Directorio para logs del sistema
```

## ⚙️ Configuración Avanzada

### Personalizar Pesos de Prioridad
Editar `config.json`:

```json
{
  "priority_weights": {
    "days_since_return": 0.4,
    "counting_delay": 0.3,
    "validation_delay": 0.2,
    "open_tablets": 0.1
  }
}
```

### Ajustar Umbrales de Alerta
```json
{
  "alert_thresholds": {
    "high_priority_days": 15,
    "critical_open_tablets": 50,
    "warning_delay_days": 10
  }
}
```

## 📊 Reportes y Exportación

### Formatos Disponibles
- **Excel (.xlsx)**: Múltiples hojas con datos y resúmenes
- **CSV**: Datos en formato plano para análisis externo
- **JSON**: Backup completo con metadatos

### Contenido de Exportación
1. **Hoja Principal**: Todos los registros con prioridades calculadas
2. **Resumen por Almacén**: KPIs y métricas agregadas
3. **Alta Prioridad**: Solo items críticos para atención inmediata

## 🔍 Casos de Uso Típicos

### Uso Diario (Supervisores)
1. Cargar reporte PDF matutino
2. Revisar dashboard de prioridades
3. Asignar recursos a items críticos
4. Exportar lista de tareas para equipos

### Análisis Semanal (Gerentes)
1. Comparar tendencias históricas
2. Identificar almacenes con problemas recurrentes
3. Generar reportes ejecutivos
4. Planificar mejoras operativas

### Auditoría Mensual (Directores)
1. Revisar KPIs de eficiencia por almacén
2. Analizar cumplimiento de SLAs
3. Identificar oportunidades de optimización
4. Generar reportes para stakeholders

## 🛠️ Solución de Problemas

### Error: "No se pudieron extraer datos del PDF"
- **Causa**: Formato de PDF no compatible
- **Solución**: Verificar que el PDF contenga texto seleccionable
- **Alternativa**: Contactar soporte para añadir compatibilidad

### Error: "Módulo no encontrado"
- **Causa**: Dependencias no instaladas
- **Solución**: Ejecutar `pip install -r requirements.txt`

### La aplicación no se abre en el navegador
- **Causa**: Puerto ocupado o firewall
- **Solución**: Intentar con `streamlit run app.py --server.port=8502`

### Datos incorrectos en el análisis
- **Causa**: Formato de fechas o números en PDF
- **Solución**: Revisar configuración regional en `config.json`

## 📞 Soporte y Contacto

Para soporte técnico o mejoras:
- 📧 Email: soporte-ti@alsinaforms.com
- 📱 WhatsApp: +1-305-XXX-XXXX
- 🌐 Portal: support.alsinaforms.com

## 🔄 Actualizaciones y Roadmap

### Próximas Funcionalidades
- 🔔 Notificaciones automáticas por email/SMS
- 📱 App móvil nativa
- 🤖 Integración con chatbots
- 📊 Machine Learning para predicciones
- 🔗 API REST para integración con otros sistemas

### Historial de Versiones
- **v1.0.0** (Actual): Funcionalidad básica completa
- **v1.1.0** (Planificada): Alertas automatizadas
- **v2.0.0** (Planificada): Integración ERP directa

---

## 📄 Licencia

© 2025 Alsina Forms Co., Inc. Todos los derechos reservados.
Esta herramienta es de uso interno exclusivo para operaciones de Alsina Forms Co.

---

**🚀 ¡Comienza a optimizar tus operaciones hoy mismo!**