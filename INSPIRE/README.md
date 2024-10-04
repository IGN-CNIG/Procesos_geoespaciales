# Documentación del proyecto

## Tabla de contenidos
- [Documentación del Módulo Inspire](documentation/INSPIRE_ES.md)
- [Documentación del Módulo de Capacidades](documentation/CAPABILITIES_ES.md)
- [Documentación del Módulo de Base de Datos](documentation/DATABASE_ES.md)
- [Documentación del módulo Logger](documentation/LOGGING_ES.md)
- [Documentación del Módulo de Informes](documentation/REPORTS_ES.md)

## Instrucciones de Instalación

Para configurar este proyecto, necesitas instalar las dependencias necesarias. Sigue los pasos a continuación:

### 1. Clonar el Repositorio

Primero, clona el repositorio en tu máquina local:

```bash
git clone https://github.com/username/your_project.git
cd your_projec
```

### 2. Crear un Entorno Virtual (Opcional pero Recomendado)

-   **Usando `venv`**:
	 -   Crea un entorno virtual de Python aislado.
    -   Actívalo según tu sistema operativo.
    -   Usa el script proporcionado para instalar GDAL y otras dependencias. 
-   **Usando Conda**:
	 -   Crea y activa un entorno Conda.
    -   Instala las dependencias directamente desde el archivo `environment.yaml` para facilitar la configuración del entorno. 
Esto asegura que tu proyecto permanezca modular y replicable entre diferentes sistemas, facilitando la gestión de dependencias y evitando conflictos.

---

#### **2.1. Entorno Virtual de Python**

**Paso 1: Crear un Entorno Virtual**

Para crear un entorno virtual llamado `venv`, ejecuta el siguiente comando:

```bash
python -m venv venv
```

**Paso 2: Activar el Entorno Virtual**

  - En Windows:
```bash
.\venv\Scripts\activate.bat
```
   - En macOS/Linux:
```bash
source venv/bin/activate.bat
```

**Paso 3: Instalar GDAL y Otras Dependencias**

Este script instala el paquete GDAL a través de un archivo de wheel (`.whl`), seguido de los paquetes listados en el archivo `requirements.txt` usando `pip`. Automatiza el proceso de instalar primero el archivo wheel y luego ejecutar el comando `pip install -r requirements.txt` directamente desde un script de Python.

Para instalar las dependencias, ejecuta:

```bash
python install_requirements.py
```

*Cómo Funciona el Script*:

-   El script utiliza el módulo `subprocess` para invocar el proceso de instalación de `pip` tanto para el archivo wheel como para los paquetes listados en `requirements.txt`.
-   Si no se encuentra el archivo wheel, el script se detiene y muestra un mensaje de error.
-   Después de que el archivo wheel se haya instalado correctamente, el script procede a instalar los paquetes del archivo `requirements.txt`.

*Características*:

-   **Instalación de Archivo Wheel**: El script puede instalar un archivo wheel específico antes de instalar otros paquetes.
-   **Manejo de Errores**: Si la instalación del archivo wheel o de los paquetes falla, el script captura el error y muestra un mensaje relevante.
-   **Rutas de Archivos Personalizadas**: Por defecto, el script busca `GDAL-3.4.3-cp311-cp311-win_amd64.whl` y `requirements.txt` en el mismo directorio. Puedes modificar este comportamiento pasando rutas de archivo personalizadas.

---

#### **2.2. Entorno Conda**

Una alternativa a usar `venv` es crear un entorno Conda. Conda gestiona tanto las dependencias como el propio intérprete de Python, lo que lo convierte en una herramienta conveniente para los entornos de proyecto.

**Paso 1: Crear un Entorno Conda**

Para crear un nuevo entorno Conda con Python 3.11, ejecuta:

```bash
conda create --name <nombre_entorno> python=3.11
```

Reemplaza `<nombre_entorno>` con el nombre deseado para tu entorno.

**Paso 2: Activar el Entorno Conda**

Una vez que se ha creado el entorno, actívalo ejecutando:

```bash
conda activate <nombre_entorno>
```

Cuando el entorno esté activado, su nombre aparecerá en tu terminal, y podrás instalar paquetes y dependencias dentro de este entorno aislado.

**Paso 3: Instalar Dependencias desde `environment.yaml`**

Para compartir o replicar la configuración del entorno en otra máquina, puedes usar el archivo `environment.yaml` para instalar todas las dependencias necesarias con un solo comando. Esto asegura la consistencia entre diferentes entornos.

Para instalar el entorno desde el archivo `environment.yaml`, ejecuta:

```bash
conda env create -f environment.yaml
```

Esto creará el entorno con las dependencias especificadas.

**Paso 4: Activar el Entorno Re-creado**

Después de crear el entorno, actívalo de la siguiente manera:

```bash
conda activate <nombre_entorno>
```

En la mayoría de los casos, el nombre del entorno está incluido en el archivo `environment.yaml` (por ejemplo, `Inspire_ENV`).



## Ejecución de Ejemplos

Para ejecutar los ejemplos proporcionados en este proyecto, utiliza la siguiente estructura de comando:

```bash
python -m examples.<nombre_del_ejemplo> 
```
#### Ejemplo

Para ejecutar un ejemplo específico, por ejemplo, `WCS_IGN.py`, ejecuta:

```bash
python -m examples.WCS_IGN
```

### Depuración de Ejemplos

Si deseas depurar los ejemplos en lugar de ejecutarlos normalmente, considera usar un depurador en tu IDE o insertar `pdb.set_trace()` en el script donde quieras pausar la ejecución.

### Notas Importantes

Asegúrate de que el entorno virtual esté activado antes de ejecutar los ejemplos para evitar problemas de dependencia.  
Asegúrate de reemplazar `<nombre_del_ejemplo>` con el nombre real del script de ejemplo que deseas ejecutar.